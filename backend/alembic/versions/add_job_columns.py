"""add job columns

Revision ID: add_job_columns
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_job_columns'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add job_title and job_summary columns to user_emails table."""
    op.add_column('user_emails', sa.Column('job_summary', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove job_title and job_summary columns from user_emails table."""
    op.drop_column('user_emails', 'job_summary')
