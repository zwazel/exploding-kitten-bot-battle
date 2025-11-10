"""Tests for database connection retry logic."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.migrations import wait_for_database


def test_wait_for_database_success_first_try() -> None:
    """Test that wait_for_database succeeds on first try when database is ready."""
    with patch("app.migrations.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        # Should complete without raising
        wait_for_database(max_retries=5, retry_delay=0.1)
        
        # Engine should be created and disposed
        assert mock_create_engine.called
        assert mock_engine.connect.called
        assert mock_engine.dispose.called


def test_wait_for_database_success_after_retries() -> None:
    """Test that wait_for_database succeeds after a few retries."""
    with patch("app.migrations.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        # Fail twice, then succeed
        call_count = [0]
        
        def connect_side_effect():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise OperationalError("Connection refused", None, None)
            return MagicMock(__enter__=lambda self: mock_conn, __exit__=lambda *args: None)
        
        mock_engine.connect.side_effect = connect_side_effect
        mock_create_engine.return_value = mock_engine
        
        # Should succeed after retries
        start_time = time.time()
        wait_for_database(max_retries=5, retry_delay=0.1)
        elapsed = time.time() - start_time
        
        # Should have taken some time for retries
        assert elapsed >= 0.1
        # Should have attempted 3 times (2 failures + 1 success)
        assert call_count[0] == 3


def test_wait_for_database_fails_after_max_retries() -> None:
    """Test that wait_for_database raises after max retries."""
    with patch("app.migrations.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        
        # Always fail
        mock_engine.connect.side_effect = OperationalError("Connection refused", None, None)
        mock_create_engine.return_value = mock_engine
        
        # Should raise OperationalError after max retries
        with pytest.raises(OperationalError):
            wait_for_database(max_retries=3, retry_delay=0.1)
        
        # Should have tried max_retries times
        assert mock_engine.connect.call_count == 3
        # Engine should be disposed even after failure
        assert mock_engine.dispose.called


def test_wait_for_database_exponential_backoff() -> None:
    """Test that wait_for_database uses exponential backoff."""
    with patch("app.migrations.create_engine") as mock_create_engine:
        with patch("app.migrations.time.sleep") as mock_sleep:
            mock_engine = MagicMock()
            
            # Fail a few times to test backoff
            call_count = [0]
            
            def connect_side_effect():
                call_count[0] += 1
                if call_count[0] <= 3:
                    raise OperationalError("Connection refused", None, None)
                return MagicMock(__enter__=lambda self: MagicMock(), __exit__=lambda *args: None)
            
            mock_engine.connect.side_effect = connect_side_effect
            mock_create_engine.return_value = mock_engine
            
            wait_for_database(max_retries=5, retry_delay=1.0)
            
            # Check that sleep was called with increasing durations
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert len(sleep_calls) == 3  # Failed 3 times before success
            
            # Each sleep should be longer than the previous (exponential backoff)
            assert sleep_calls[0] < sleep_calls[1] < sleep_calls[2]


def test_wait_for_database_caps_at_10_seconds() -> None:
    """Test that wait_for_database caps retry delay at 10 seconds."""
    with patch("app.migrations.create_engine") as mock_create_engine:
        with patch("app.migrations.time.sleep") as mock_sleep:
            mock_engine = MagicMock()
            
            # Fail many times to test cap
            call_count = [0]
            
            def connect_side_effect():
                call_count[0] += 1
                if call_count[0] <= 10:
                    raise OperationalError("Connection refused", None, None)
                return MagicMock(__enter__=lambda self: MagicMock(), __exit__=lambda *args: None)
            
            mock_engine.connect.side_effect = connect_side_effect
            mock_create_engine.return_value = mock_engine
            
            wait_for_database(max_retries=15, retry_delay=1.0)
            
            # Check that sleep was called with capped durations
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            
            # No sleep should exceed 10 seconds
            assert all(sleep <= 10.0 for sleep in sleep_calls)
