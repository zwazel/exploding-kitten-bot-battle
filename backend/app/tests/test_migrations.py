"""Tests for database migrations and schema validation."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

from app.database import engine
from app.migrations import run_migrations
from app.models import Base


def test_migrations_create_all_tables() -> None:
    """Test that migrations create all expected tables."""
    # Run migrations
    run_migrations()
    
    # Get inspector
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    # Check that all expected tables exist
    expected_tables = {"users", "bots", "bot_versions", "replays", "replay_participants", "alembic_version"}
    assert expected_tables.issubset(set(table_names)), f"Missing tables: {expected_tables - set(table_names)}"


def test_users_table_has_username_column() -> None:
    """Test that the users table has the username column (regression test)."""
    # Run migrations
    run_migrations()
    
    # Get inspector
    inspector = inspect(engine)
    columns = inspector.get_columns("users")
    column_names = {col["name"] for col in columns}
    
    # Check that username column exists
    assert "username" in column_names, "users table missing 'username' column"
    
    # Check all expected columns
    expected_columns = {"id", "email", "username", "display_name", "password_hash", "created_at"}
    assert expected_columns.issubset(column_names), f"Missing columns: {expected_columns - column_names}"


def test_users_table_has_unique_constraints() -> None:
    """Test that the users table has proper unique constraints."""
    # Run migrations
    run_migrations()
    
    # Get inspector
    inspector = inspect(engine)
    unique_constraints = inspector.get_unique_constraints("users")
    indexes = inspector.get_indexes("users")
    
    # Collect all columns with unique constraints
    unique_columns = set()
    for constraint in unique_constraints:
        unique_columns.update(constraint.get("column_names", []))
    
    for index in indexes:
        if index.get("unique"):
            unique_columns.update(index.get("column_names", []))
    
    # Check that email and username have unique constraints
    assert "email" in unique_columns, "users.email should have unique constraint"
    assert "username" in unique_columns, "users.username should have unique constraint"


def test_all_model_tables_exist() -> None:
    """Test that all models defined in Base have corresponding tables."""
    # Run migrations
    run_migrations()
    
    # Get inspector
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    # Get all tables from metadata
    metadata_tables = set(Base.metadata.tables.keys())
    
    # Check that all metadata tables exist (excluding alembic_version which is created separately)
    assert metadata_tables.issubset(existing_tables), f"Missing tables: {metadata_tables - existing_tables}"


def test_migrations_are_idempotent() -> None:
    """Test that running migrations multiple times doesn't cause errors."""
    # Run migrations twice
    run_migrations()
    run_migrations()
    
    # Should complete without errors
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert "users" in table_names


@pytest.mark.parametrize("table_name,expected_columns", [
    ("users", ["id", "email", "username", "display_name", "password_hash", "created_at"]),
    ("bots", ["id", "user_id", "name", "created_at", "current_version_id"]),
    ("bot_versions", ["id", "bot_id", "version_number", "created_at", "file_path", "archived", "file_hash"]),
    ("replays", ["id", "created_at", "file_path", "winner_name", "summary"]),
    ("replay_participants", ["id", "replay_id", "bot_version_id", "bot_label", "placement", "is_winner"]),
])
def test_table_columns_exist(table_name: str, expected_columns: list[str]) -> None:
    """Test that each table has all expected columns."""
    # Run migrations
    run_migrations()
    
    # Get inspector
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    column_names = {col["name"] for col in columns}
    
    # Check that all expected columns exist
    missing_columns = set(expected_columns) - column_names
    assert not missing_columns, f"{table_name} missing columns: {missing_columns}"
