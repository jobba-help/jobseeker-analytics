from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
import sqlalchemy as sa
from db.users import Users
import uuid

FINISHED = "finished"
STARTED = "started"
PENDING = "pending"
FAILED = "failed"


class TaskRuns(SQLModel, table=True):
    __tablename__ = "processing_task_runs"
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.user_id")
    created: datetime = Field(default_factory=datetime.now, nullable=False)
    updated: datetime = Field(
        sa_column_kwargs={"onupdate": sa.func.now()},
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    status: str = Field(nullable=False)
    task_type: str = Field(default="email_processing")  # email_processing or job_scraping
    total_emails: int = 0
    processed_emails: int = 0
    result: str = Field(default=None, nullable=True)  # JSON string for storing task results
    error: str = Field(default=None, nullable=True)  # Error message if task failed

    user: Users = Relationship()
