import datetime
import logging
import os

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from contextlib import asynccontextmanager

from db.users import UserData
from db.utils.user_utils import add_user
from utils.file_utils import get_user_filepath
from utils.config_utils import get_settings
from session.session_layer import validate_session
from database import create_db_and_tables

# Import routes
from routes import playground_routes, email_routes, auth_routes, file_routes, users_routes, email_webhook

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
settings = get_settings()
APP_URL = settings.APP_URL
app.add_middleware(SessionMiddleware, secret_key=settings.COOKIE_SECRET)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routes
app.include_router(auth_routes.router)
app.include_router(playground_routes.router)
app.include_router(email_routes.router)
app.include_router(file_routes.router)
app.include_router(users_routes.router)
app.include_router(email_webhook.router, prefix="/api/v1")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter  # Ensure limiter is assigned

# Configure CORS
if settings.is_publicly_deployed:
    # Production CORS settings
    origins = ["https://www.jobba.help", "https://www.staging.jobba.help"]
else:
    # Development CORS settings
    origins = [
        "http://localhost:3000",  # Assuming frontend runs on port 3000
        "http://127.0.0.1:3000",
    ]

# Add SlowAPI middleware for rate limiting
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow frontend origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")


# Rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    raise HTTPException(
        status_code=429,
        detail="Too many requests. Please try again later.",
    )


@app.get("/ping")
@limiter.limit("1/minute")
def ping(request: Request):
    """Test endpoint to verify the server is running"""
    return {"status": "success", "message": "Server is running"}


@app.post("/api/add-user")
async def add_user_endpoint(user_data: UserData):
    """
    This endpoint adds a user to the database
    """
    try:
        add_user(user_data)
        return {"message": "User added successfully"}
    except Exception as e:
        # Log the error for debugging purposes
        logger.error(f"An error occurred while adding user: {e}")
        return {"error": "An error occurred while adding the user."}


@app.get("/")
async def root(request: Request, response_class=HTMLResponse):
    return templates.TemplateResponse("homepage.html", {"request": request})


@app.get("/download-file")
async def download_file(request: Request, user_id: str = Depends(validate_session)):
    if not user_id:
        return RedirectResponse("/logout", status_code=303)
    directory = get_user_filepath(user_id)
    filename = "emails.csv"
    filepath = f"{directory}/{filename}"
    if os.path.exists(filepath):
        logger.info("user_id:%s downloading from filepath %s", user_id, filepath)
        return FileResponse(filepath)
    return HTMLResponse(content="File not found :( ", status_code=404)


@app.get("/success", response_class=HTMLResponse)
def success(request: Request, user_id: str = Depends(validate_session)):
    if not user_id:
        return RedirectResponse("/logout", status_code=303)
    today = str(datetime.date.today())
    return templates.TemplateResponse(
        "success.html", {"request": request, "today": today}
    )


# Run the app using Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
