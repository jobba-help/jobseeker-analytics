from sqlmodel import SQLModel, Field
from datetime import datetime

class UserEmails(SQLModel, table=True):
    __tablename__ = "user_emails"  
    id: str = Field(primary_key=True)  # Gmail email ID (not unique globally)
    user_id: str = Field(primary_key=True)  # Unique per user (composite key)
    company_name: str
    application_status: str
    received_at: datetime
    subject: str
    job_title: str
    email_from: str  # to avoid 'from' being a reserved key word
    job_summary: str = Field(default="")  # Summary of the job description