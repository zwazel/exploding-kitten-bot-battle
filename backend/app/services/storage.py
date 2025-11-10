"""Helpers for working with the filesystem storage."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from fastapi import UploadFile

from ..config import get_settings


settings = get_settings()


class StorageManager:
    """Utility wrapper around the configured storage directory."""

    def __init__(self) -> None:
        self.root = settings.storage_root
        self.bot_root = self.root / "bots"
        self.replay_root = self.root / "replays"
        self.bot_root.mkdir(parents=True, exist_ok=True)
        self.replay_root.mkdir(parents=True, exist_ok=True)

    def user_bot_directory(self, user_id: int) -> Path:
        path = self.bot_root / f"user_{user_id}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_bot_file(self, user_id: int, version_number: int, upload: UploadFile) -> Path:
        destination = self.user_bot_directory(user_id) / f"version_{version_number}.py"
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        return destination

    def archive_bot_files(self, paths: Iterable[Path]) -> None:
        for path in paths:
            if path.exists():
                path.unlink()

    def new_replay_path(self) -> Path:
        return self.replay_root / f"replay_{uuid4().hex}.json"


__all__ = ["StorageManager"]
