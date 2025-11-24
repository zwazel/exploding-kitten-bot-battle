"""add_username_column_if_missing

This migration adds the username column to the users table if it doesn't exist.
This handles the case where users have an old database schema from before
the username column was added.

Revision ID: 2de4843f4caa
Revises: 90b321684f03
Create Date: 2025-11-10 15:44:09.646062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '2de4843f4caa'
down_revision: Union[str, Sequence[str], None] = '90b321684f03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema.
    
    Adds the username column to users table if it doesn't exist.
    This is idempotent and safe to run on databases that already have the column.
    """
    # Get connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if users table exists
    if 'users' not in inspector.get_table_names():
        # Table doesn't exist, skip (will be created by initial_schema migration)
        return
    
    # Check if username column already exists
    columns = inspector.get_columns('users')
    column_names = {col['name'] for col in columns}
    
    if 'username' not in column_names:
        # Add the username column
        # Note: For PostgreSQL and MySQL, we can add with constraints directly
        # For SQLite, we need to be more careful with constraints
        try:
            with op.batch_alter_table('users', schema=None) as batch_op:
                batch_op.add_column(sa.Column('username', sa.String(length=120), nullable=True))
            
            # For existing rows, set username to a default value based on display_name or email
            # Users will need to update this if needed
            conn.execute(sa.text("""
                UPDATE users 
                SET username = LOWER(REPLACE(REPLACE(display_name, ' ', '_'), '-', '_'))
                WHERE username IS NULL
            """))
            
            # Now make it NOT NULL and add unique constraint
            with op.batch_alter_table('users', schema=None) as batch_op:
                batch_op.alter_column('username', nullable=False)
                batch_op.create_unique_constraint('uq_users_username', ['username'])
                
        except Exception as e:
            # If this fails (e.g., column already exists), log but continue
            print(f"Note: Could not add username column (may already exist): {e}")


def downgrade() -> None:
    """
    Downgrade schema.
    
    Removes the username column from users table if it exists.
    """
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'users' not in inspector.get_table_names():
        return
    
    columns = inspector.get_columns('users')
    column_names = {col['name'] for col in columns}
    
    if 'username' in column_names:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_constraint('uq_users_username', type_='unique')
            batch_op.drop_column('username')
