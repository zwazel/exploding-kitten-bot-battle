"""Bot management endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import models
from ..dependencies import get_current_user
from ..schemas import BotProfile, BotVersionSummary, ReplayParticipantSummary, ReplaySummary, UploadResponse
from ..services.match_runner import run_match
from ..services.storage import StorageManager
from ..services.bot_loader import require_bot
from ..database import get_db

router = APIRouter(prefix="/bots", tags=["bots"])

storage = StorageManager()


def _bot_version_summary(version: models.BotVersion, active_id: int) -> BotVersionSummary:
    return BotVersionSummary(
        id=version.id,
        version_number=version.version_number,
        created_at=version.created_at,
        is_active=version.id == active_id,
    )


def _replay_summary(replay: models.Replay) -> ReplaySummary:
    return ReplaySummary(
        id=replay.id,
        created_at=replay.created_at,
        winner_name=replay.winner_name,
        participants=[
            ReplayParticipantSummary(
                bot_label=p.bot_label,
                placement=p.placement,
                is_winner=p.is_winner,
            )
            for p in replay.participants
        ],
        summary=replay.summary,
    )


@router.get("/me", response_model=BotProfile)
def my_bot(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BotProfile:
    bot = current_user.bot
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot profile missing")

    versions = sorted(bot.versions, key=lambda v: v.version_number)
    version_summaries = [_bot_version_summary(v, bot.current_version_id or -1) for v in versions]

    replays_query = (
        db.query(models.Replay)
        .join(models.ReplayParticipant)
        .join(models.BotVersion, models.ReplayParticipant.bot_version_id == models.BotVersion.id)
        .filter(models.BotVersion.bot_id == bot.id)
        .order_by(models.Replay.created_at.desc())
        .limit(20)
        .all()
    )
    replays = [_replay_summary(r) for r in replays_query]

    return BotProfile(
        bot_id=bot.id,
        current_version=_bot_version_summary(bot.current_version, bot.current_version_id) if bot.current_version else None,
        versions=version_summaries,
        recent_replays=replays,
    )


@router.post("/upload", response_model=UploadResponse)
def upload_bot(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResponse:
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .py files are supported")

    bot = current_user.bot
    if bot is None:
        bot = models.Bot(user_id=current_user.id)
        db.add(bot)
        db.flush()

    next_version = (bot.versions[-1].version_number + 1) if bot.versions else 1

    saved_path = storage.save_bot_file(current_user.id, next_version, file)

    # Ensure the file loads before committing
    require_bot(saved_path, f"user_{current_user.id}_{next_version}", f"{current_user.display_name} v{next_version}")

    old_versions = [v for v in bot.versions if v.file_path]
    old_paths = [Path(v.file_path) for v in old_versions if v.file_path]

    version = models.BotVersion(
        bot_id=bot.id,
        version_number=next_version,
        file_path=str(saved_path),
    )
    db.add(version)
    db.flush()

    bot.current_version_id = version.id
    db.add(bot)

    # Archive previous files but keep metadata
    for old in old_versions:
        old.archived = True
        old.file_path = None
        db.add(old)

    storage.archive_bot_files(old_paths)
    db.flush()

    try:
        match_result = run_match(db, version, storage)
    except Exception:
        db.rollback()
        storage.archive_bot_files([saved_path])
        raise

    response = UploadResponse(
        bot_version=_bot_version_summary(version, version.id),
        replay=_replay_summary(match_result.replay),
    )

    return response


__all__ = ["router"]
