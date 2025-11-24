"""Bot management endpoints."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
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
    BotUploadResponse,
    BotUploadStatus,
    BotVersionSummary,
    ReplayParticipantSummary,
    ReplaySummary,
)
from ..services.bot_loader import require_bot
from ..services.bot_versions import compute_file_hash
from ..services.storage import StorageManager
from ..utils import clean_identifier, enforce_bot_name

router = APIRouter(prefix="/bots", tags=["bots"])

storage = StorageManager()


def _bot_version_summary(version: models.BotVersion, active_id: int) -> BotVersionSummary:
    return BotVersionSummary(
        id=version.id,
        version_number=version.version_number,
        created_at=version.created_at,
        is_active=version.id == active_id,
        file_hash=version.file_hash,
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


def _derive_bot_name(filename: str) -> str:
    stem = Path(filename).stem
    if not stem:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to derive bot name from filename",
        )
    try:
        cleaned = clean_identifier(stem)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot filename must contain alphanumeric characters",
        ) from exc
    try:
        return enforce_bot_name(cleaned)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/upload", response_model=BotUploadResponse)
def upload_bot(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BotUploadResponse:
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .py files are supported",
        )

    bot_name = _derive_bot_name(file.filename)

    bot = (
        db.query(models.Bot)
        .filter(models.Bot.user_id == current_user.id)
        .filter(models.Bot.name == bot_name)
        .first()
    )
    if not bot:
        bot = models.Bot(user_id=current_user.id, name=bot_name)
        bot.owner = current_user
        db.add(bot)
        db.flush()

    content = file.file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    with NamedTemporaryFile("wb", suffix=".py", delete=False) as handle:
        handle.write(content)
        temp_path = Path(handle.name)

    try:
        require_bot(temp_path, f"user_{current_user.id}_{bot.id}", bot.qualified_name)
        file_hash = compute_file_hash(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)

    previous_active = bot.current_version_id
    matching_version = next(
        (version for version in bot.versions if version.file_hash == file_hash),
        None,
    )

    if matching_version:
        stored_path = Path(matching_version.file_path or "")
        if not stored_path.exists():
            restored = storage.write_bot_file(
                current_user.id, bot.id, matching_version.version_number, content
            )
            matching_version.file_path = str(restored)
            db.add(matching_version)
        bot.current_version_id = matching_version.id
        db.add(bot)
        status = (
            BotUploadStatus.UNCHANGED
            if previous_active == matching_version.id
            else BotUploadStatus.REVERTED
        )
        db.flush()
        db.refresh(bot)
        version_summary = _bot_version_summary(matching_version, bot.current_version_id or -1)
    else:
        next_version = (
            max((version.version_number for version in bot.versions), default=0) + 1
        )
        saved_path = storage.write_bot_file(current_user.id, bot.id, next_version, content)
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
        db.flush()
        db.refresh(bot)

        status = (
            BotUploadStatus.CREATED if next_version == 1 else BotUploadStatus.NEW_VERSION
        )
        version_summary = _bot_version_summary(version, bot.current_version_id or -1)

    summary = _bot_summary(bot)

    return BotUploadResponse(status=status, bot=summary, version=version_summary)


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bot(
    bot_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    bot = _get_user_bot(db, current_user, bot_id)
    paths = [Path(v.file_path) for v in bot.versions if v.file_path]
    storage.archive_bot_files(paths)
    db.delete(bot)
    db.flush()


__all__ = ["router"]
