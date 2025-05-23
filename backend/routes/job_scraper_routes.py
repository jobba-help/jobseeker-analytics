import os
from playwright.sync_api import sync_playwright
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
from utils.config_utils import get_settings
from utils.task_utils import create_task, update_task
from session.session_layer import validate_session
from typing import List, Dict, Tuple
import requests
from datetime import datetime
import database
import json
from sqlmodel import Session
from db.processing_tasks import TaskRuns, PENDING, STARTED, FINISHED, FAILED
import openai

limiter = Limiter(key_func=get_remote_address)

# Logger setup
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()
APP_URL = settings.APP_URL
GOOGLE_CSE_API_KEY = settings.GOOGLE_CSE_API_KEY
GOOGLE_CSE_ID = settings.GOOGLE_CSE_ID
OPENAI_API_KEY = settings.OPENAI_API_KEY

# FastAPI router
router = APIRouter()

def search_job_postings(company_name: str, job_title: str) -> List[Dict[str, str]]:
    """
    Search for job postings using Google Custom Search Engine.
    
    Args:
        company_name: Name of the company
        job_title: Job title to search for
    
    Returns:
        List of dictionaries containing search results with title, url, and snippet
    """
    search_query = f"{company_name} {job_title} job posting"
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_CSE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": search_query,
        "num": 10  # Number of results to return
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        return results
    except Exception as e:
        logger.error(f"Error searching job postings: {str(e)}")
        return []

def select_relevant_job_url(search_results: List[Dict[str, str]], company_name: str, job_title: str) -> str:
    """
    Use OpenAI to analyze search results and select the most relevant job posting URL.
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    # Format search results as a string
    search_results_text = "\n".join([
        f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
        for r in search_results
    ])
    
    prompt = f"""
    Given the following Google search results for "{company_name} {job_title}", 
    select the most relevant job posting URL. Consider:
    1. Official company career pages or ATS systems (like Greenhouse, Workday, etc.)
    2. Relevance to the specific company and job title
    3. Recency of the posting
    
    Search Results:
    {search_results_text}
    
    Return only the URL of the most relevant job posting.
    """
    logger.info(f"Model: {settings.OPENAI_MODEL}")
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a job search assistant that helps identify the most relevant job posting URLs."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    return response.choices[0].message.content.strip()

def scrape_job_description(url: str, task_id: str, db_session: Session) -> None:
    """
    Scrape the job description from the given URL using Browserbase.
    Updates task status and results in the database.
    
    Args:
        url: URL of the job posting to scrape
        task_id: ID of the task to update
        db_session: Database session for updating task status
    """
    # Get or create a Browserbase session
    bb_session = settings.get_browserbase_session()
    logger.info(f"Using Browserbase session: {bb_session.id}")
    logger.info(f"Session replay URL: https://browserbase.com/sessions/{bb_session.id}")

    try:
        # Update task status to STARTED
        update_task(db_session, task_id, STARTED)
        logger.info(f"Updated task {task_id} status to {STARTED}")

        with sync_playwright() as playwright:
            # Connect to the remote session
            chromium = playwright.chromium
            browser = chromium.connect_over_cdp(bb_session.connect_url)
            context = browser.contexts[0]
            page = context.pages[0]

            # Navigate to the job posting
            page.goto(url)
            
            # Extract the job description
            raw_description = page.inner_text()
            
            # Generate summary
            summary = summarize_job_description(raw_description)
            
            # Update task with results
            update_task(db_session, task_id, FINISHED, result={
                "raw_description": raw_description,
                "summary": summary,
                "url": url
            })
            logger.info(f"Updated task {task_id} status to {FINISHED} with results")
            
    except Exception as e:
        logger.error(f"Error scraping job description: {str(e)}")
        update_task(db_session, task_id, FAILED, error=str(e))

    finally:
        # Close the browser
        if 'page' in locals():
            page.close()
        if 'browser' in locals():
            browser.close()
        logger.info("Browser session closed")

def summarize_job_description(description: str) -> str:
    """
    Use OpenAI to generate a concise summary of the job description.
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
    Please provide a concise summary of this job description, focusing on:
    1. Key responsibilities
    2. Required qualifications
    3. Preferred qualifications
    4. Any notable benefits or company information
    
    Job Description:
    {description}
    
    Format the summary in clear sections with bullet points.
    """
    logger.info(f"Model: {settings.OPENAI_MODEL}")
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a job description analyzer that creates clear, concise summaries."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content.strip()

@router.post("/tasks")
@limiter.limit("5/minute")
async def create_scraping_task(
    request: Request,
    db_session: database.DBSession,
    user_id: str = Depends(validate_session)
):
    """
    Create a new job scraping task.
    
    Request body:
    {
        "url": "https://example.com/job/123"
    }
    
    Response:
    {
        "task_id": "uuid",
        "status": "pending"
    }

    To create a task, you can use the following curl command:
    curl -X POST "http://localhost:8000/tasks" -H "Content-Type: application/json" -d '{"url": "https://example.com/job/123"}'
    """
    data = await request.json()
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    task = create_task(request, db_session, "scrape_job_description", user_id)
        
    # Add the scraping task to background tasks after commit
    settings.background_tasks.add_task(
        scrape_job_description,
        url=url,
        task_id=task.task_id,
        db_session=db_session
    )
    response = JSONResponse(content={"task_id": task.task_id,
        "status": PENDING})
    response.background = settings.background_tasks
    return response

@router.get("/tasks/{task_id}")
@limiter.limit("5/minute")
async def get_task_status(
    request: Request,
    task_id: str,
    user_id: str = Depends(validate_session)
):
    """
    Get the status and results of a scraping task.
    
    Response:
    {
        "status": "pending|started|finished|failed",
        "created_at": "ISO timestamp",
        "updated_at": "ISO timestamp",
        "result": {
            "raw_description": "string",
            "summary": "string",
            "url": "string"
        },
        "error": "string (if failed)"
    }
    To get the status of a task, you can use the following curl command:
    curl -X GET "http://localhost:8000/tasks/123"
    """
    return await _get_task_status(task_id, user_id)

async def _get_task_status(task_id: str, user_id: str):
    """Internal function to get task status, can be called directly or via endpoint."""
    with Session(database.engine) as db_session:
        task = db_session.get(TaskRuns, task_id)
        if not task or task.user_id != user_id or task.task_type != "job_scraping":
            raise HTTPException(status_code=404, detail="Task not found")
        
        response = {
            "status": task.status,
            "created_at": task.created.isoformat(),
            "updated_at": task.updated.isoformat()
        }
        
        if task.result:
            response["result"] = json.loads(task.result)
        if task.error:
            response["error"] = task.error
            
        return response
