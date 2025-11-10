"""Shared helpers for managing bot versions."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, List

from sqlalchemy.orm import Session

from .. import models


def compute_file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_versions(db: Session, versions: Iterable[models.BotVersion]) -> List[Path]:
    archived_paths: List[Path] = []
    for version in versions:
        if version.file_path:
            archived_paths.append(Path(version.file_path))
        version.archived = True
        version.file_path = None
        db.add(version)
    return archived_paths


__all__ = ["archive_versions", "compute_file_hash"]
