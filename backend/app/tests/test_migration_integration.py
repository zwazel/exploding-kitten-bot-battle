"""Integration test to verify migrations fix the schema issue."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Base, User


def test_migration_fixes_missing_username_column() -> None:
    """
    Integration test: Simulate the exact issue users were experiencing.
    
    This test:
    1. Creates a database with the old schema (without username column)
    2. Runs migrations to add the missing column
    3. Verifies that signup/login works correctly
    """
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        
        # Step 1: Create old schema (without username column)
        # Simulate what an old database looked like
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    display_name VARCHAR(120) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
            """))
            conn.commit()
        
        # Verify old schema doesn't have username column
        with engine.begin() as conn:
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            assert "username" not in columns, "Test setup error: username shouldn't exist yet"
        
        # Step 2: Run migrations with the test database
        # Set environment variable to use our test database
        old_db_url = os.environ.get("ARENA_DATABASE_URL")
        os.environ["ARENA_DATABASE_URL"] = db_url
        
        try:
            # Clear the settings cache to pick up new database URL
            from app.config import get_settings
            get_settings.cache_clear()
            
            # Run migrations
            from app.migrations import run_migrations
            run_migrations()
            
        finally:
            # Restore original database URL
            if old_db_url:
                os.environ["ARENA_DATABASE_URL"] = old_db_url
            else:
                os.environ.pop("ARENA_DATABASE_URL", None)
            get_settings.cache_clear()
        
        # Step 3: Verify new schema has username column
        with engine.begin() as conn:
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            assert "username" in columns, "Migration failed to add username column"
        
        # Step 4: Verify we can now create users (like in signup)
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            # This would have failed before with "column username does not exist"
            user = User(
                email="test@example.com",
                username="testuser",
                display_name="Test User",
                password_hash="hashed_password",
            )
            session.add(user)
            session.commit()
            
            # Verify user was created
            retrieved_user = session.query(User).filter(User.email == "test@example.com").first()
            assert retrieved_user is not None
            assert retrieved_user.username == "testuser"
            assert retrieved_user.display_name == "Test User"
            
        finally:
            session.close()
        
    finally:
        # Cleanup
        if Path(db_path).exists():
            Path(db_path).unlink()


if __name__ == "__main__":
    test_migration_fixes_missing_username_column()
    print("✅ Integration test passed: Migrations successfully fix the missing username column issue")
