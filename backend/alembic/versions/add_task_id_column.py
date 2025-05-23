"""add task_id column

Revision ID: add_task_id_column
Revises: add_job_columns
Create Date: 2024-03-19 11:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_task_id_column'
down_revision: Union[str, None] = 'add_job_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add task_id column and make it the primary key."""
    # Add task_id column
    op.add_column('processing_task_runs', sa.Column('task_id', sa.String(36), nullable=True))
    
    # Generate UUIDs for existing rows
    op.execute("UPDATE processing_task_runs SET task_id = gen_random_uuid()::text")
    
    # Make task_id not nullable
    op.alter_column('processing_task_runs', 'task_id', nullable=False)
    
    # Drop the primary key constraint
    op.execute('ALTER TABLE processing_task_runs DROP CONSTRAINT processing_task_runs_pkey')
    
    # Add new primary key constraint
    op.create_primary_key('processing_task_runs_pkey', 'processing_task_runs', ['task_id'])
    
    # Add index on user_id for faster lookups
    op.create_index('ix_processing_task_runs_user_id', 'processing_task_runs', ['user_id'])


def downgrade() -> None:
    """Remove task_id column and restore user_id as primary key."""
    # Drop the primary key constraint
    op.execute('ALTER TABLE processing_task_runs DROP CONSTRAINT processing_task_runs_pkey')
    
    # Drop the user_id index
    op.drop_index('ix_processing_task_runs_user_id')
    
    # Make user_id the primary key again
    op.create_primary_key('processing_task_runs_pkey', 'processing_task_runs', ['user_id'])
    
    # Drop the task_id column
    op.drop_column('processing_task_runs', 'task_id') 