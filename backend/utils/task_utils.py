from db.processing_tasks import TaskRuns, STARTED, FINISHED, FAILED, PENDING
from sqlmodel import Session
from typing import Dict, Optional
import json
import logging
from fastapi import Request, Depends
from session.session_layer import validate_session

logger = logging.getLogger(__name__)

def create_task(request: Request, db_session: Session, task_type: str, user_id: int) -> TaskRuns:
    """Create a new task in the database and return it."""
    logger.info(f"Creating task for user {user_id} with type {task_type}")
    task = TaskRuns(
        user_id=user_id,
        status=PENDING,
        task_type=task_type
    )
    db_session.add(task)
    db_session.commit()
    return task

def update_task(db_session: Session, task_id: str, status: str, result: Optional[Dict] = None, error: Optional[str] = None) -> Optional[TaskRuns]:
    """Update task status and results in the database."""
    logger.info(f"Updating task {task_id} with status {status} and result {result}")
    task = db_session.get(TaskRuns, task_id)
    if task:
        task.status = status
        if result:
            task.result = json.dumps(result)
        if error:
            task.error = error
        db_session.commit()
    return task
