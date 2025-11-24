"""Database migration utilities."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from .config import get_settings

logger = logging.getLogger(__name__)


def wait_for_database(max_retries: int = 30, retry_delay: float = 1.0) -> None:
    """
    Wait for the database to be ready to accept connections.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Initial delay between retries in seconds (will increase exponentially)
    
    Raises:
        OperationalError: If database is not ready after max_retries
    """
    settings = get_settings()
    logger.info(f"Waiting for database to be ready at {settings.database_url.split('@')[-1]}...")
    
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    
    for attempt in range(1, max_retries + 1):
        try:
            # Try to connect and execute a simple query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database is ready!")
            engine.dispose()
            return
        except OperationalError as e:
            if attempt == max_retries:
                logger.error(f"Database not ready after {max_retries} attempts")
                engine.dispose()
                raise
            
            # Calculate exponential backoff with jitter
            wait_time = min(retry_delay * (1.5 ** (attempt - 1)), 10.0)
            logger.warning(
                f"Database not ready (attempt {attempt}/{max_retries}): {e}. "
                f"Retrying in {wait_time:.1f}s..."
            )
            time.sleep(wait_time)
    
    engine.dispose()


def run_migrations() -> None:
    """Run all pending database migrations."""
    # Get the backend directory (parent of app directory)
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini = backend_dir / "alembic.ini"
    
    if not alembic_ini.exists():
        logger.warning(f"Alembic configuration not found at {alembic_ini}")
        return
    
    # Wait for database to be ready
    try:
        wait_for_database()
    except OperationalError:
        logger.error("Database connection failed. Cannot run migrations.")
        raise
    
    logger.info("Running database migrations...")
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise


__all__ = ["run_migrations", "wait_for_database"]
