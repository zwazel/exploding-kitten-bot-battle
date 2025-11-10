"""Bot management endpoints."""

from __future__ import annotations

from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..dependencies import get_current_user
from ..schemas import (
    BotCreateRequest,
    BotProfile,
    BotSummary,
    BotVersionSummary,
    ReplayParticipantSummary,
    ReplaySummary,
    UploadResponse,
)
from ..services.bot_loader import require_bot
from ..services.bot_versions import archive_versions, compute_file_hash
from ..services.match_runner import run_match
from ..services.storage import StorageManager
from ..utils import enforce_bot_name

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


def _bot_summary(bot: models.Bot) -> BotSummary:
    active_id = bot.current_version_id or -1
    current = bot.current_version if bot.current_version else None
    return BotSummary(
        id=bot.id,
        name=bot.name,
        qualified_name=bot.qualified_name,
        created_at=bot.created_at,
        current_version=_bot_version_summary(current, active_id) if current else None,
    )


def _bot_detail(bot: models.Bot, db: Session) -> BotProfile:
    versions = sorted(bot.versions, key=lambda v: v.version_number)
    summaries = [_bot_version_summary(v, bot.current_version_id or -1) for v in versions]
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
        id=bot.id,
        name=bot.name,
        qualified_name=bot.qualified_name,
        created_at=bot.created_at,
        current_version=_bot_version_summary(bot.current_version, bot.current_version_id)
        if bot.current_version
        else None,
        versions=summaries,
        recent_replays=replays,
    )


def _get_user_bot(db: Session, user: models.User, bot_id: int) -> models.Bot:
    bot = db.get(models.Bot, bot_id)
    if bot is None or bot.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    return bot


@router.get("", response_model=List[BotSummary])
def list_bots(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[BotSummary]:
    bots = (
        db.query(models.Bot)
        .filter(models.Bot.user_id == current_user.id)
        .order_by(models.Bot.created_at.asc())
        .all()
    )
    return [_bot_summary(bot) for bot in bots]


@router.post("", response_model=BotSummary, status_code=status.HTTP_201_CREATED)
def create_bot(
    payload: BotCreateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BotSummary:
    try:
        normalized = enforce_bot_name(payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    existing = (
        db.query(models.Bot)
        .filter(models.Bot.user_id == current_user.id)
        .filter(models.Bot.name == normalized)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bot name already in use")

    bot = models.Bot(user_id=current_user.id, name=normalized)
    bot.owner = current_user
    db.add(bot)
    db.flush()

    return _bot_summary(bot)


@router.get("/{bot_id}", response_model=BotProfile)
def get_bot(
    bot_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BotProfile:
    bot = _get_user_bot(db, current_user, bot_id)
    return _bot_detail(bot, db)


@router.post("/{bot_id}/upload", response_model=UploadResponse)
def upload_bot_version(
    bot_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResponse:
    bot = _get_user_bot(db, current_user, bot_id)

    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .py files are supported")

    next_version = (bot.versions[-1].version_number + 1) if bot.versions else 1
    saved_path = storage.save_bot_file(current_user.id, bot.id, next_version, file)

    try:
        require_bot(saved_path, f"user_{current_user.id}_{bot.id}_{next_version}", bot.qualified_name)
    except Exception:
        storage.archive_bot_files([saved_path])
        raise

    file_hash = compute_file_hash(saved_path)

    old_versions = [v for v in bot.versions if v.file_path]
    old_paths = archive_versions(db, old_versions)

    version = models.BotVersion(
        bot_id=bot.id,
        version_number=next_version,
        file_path=str(saved_path),
        file_hash=file_hash,
    )
    db.add(version)
    db.flush()

    bot.current_version_id = version.id
    db.add(bot)

    storage.archive_bot_files(old_paths)
    db.flush()

    try:
        match_result = run_match(db, version, storage)
    except Exception:
        db.rollback()
        storage.archive_bot_files([saved_path])
        raise

    return UploadResponse(
        bot_version=_bot_version_summary(version, version.id),
        replay=_replay_summary(match_result.replay),
    )


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bot(
    bot_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    bot = _get_user_bot(db, current_user, bot_id)
    old_paths = archive_versions(db, [v for v in bot.versions if v.file_path])
    storage.archive_bot_files(old_paths)
    db.delete(bot)
    db.flush()


__all__ = ["router"]
