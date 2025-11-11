"""Shared helpers for managing bot versions."""

from __future__ import annotations

import hashlib
from pathlib import Path
def compute_file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["compute_file_hash"]
