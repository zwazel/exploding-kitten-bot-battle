"""Replay metadata and file endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models
from ..dependencies import get_current_user
from ..database import get_db
from ..schemas import ReplaySummary, ReplayParticipantSummary

router = APIRouter(prefix="/replays", tags=["replays"])


def _summary(record: models.Replay) -> ReplaySummary:
    return ReplaySummary(
        id=record.id,
        created_at=record.created_at,
        winner_name=record.winner_name,
        participants=[
            ReplayParticipantSummary(
                bot_label=participant.bot_label,
                placement=participant.placement,
                is_winner=participant.is_winner,
            )
            for participant in record.participants
        ],
        summary=record.summary,
    )


@router.get("/{replay_id}", response_model=ReplaySummary)
def get_replay(
    replay_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReplaySummary:
    replay = db.get(models.Replay, replay_id)
    if replay is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Replay not found")

    owned_versions = {
        version.id
        for bot in current_user.bots
        for version in bot.versions
    } if current_user.bots else set()
    if owned_versions:
        participant_version_ids = {
            p.bot_version_id for p in replay.participants if p.bot_version_id is not None
        }
        if not participant_version_ids & owned_versions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to replay")

    return _summary(replay)


@router.get("/{replay_id}/file")
def download_replay(
    replay_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    replay = db.get(models.Replay, replay_id)
    if replay is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Replay not found")

    owned_versions = {
        version.id
        for bot in current_user.bots
        for version in bot.versions
    } if current_user.bots else set()
    if owned_versions:
        participant_version_ids = {
            p.bot_version_id for p in replay.participants if p.bot_version_id is not None
        }
        if not participant_version_ids & owned_versions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to replay")

    path = Path(replay.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Replay file is no longer available")

    return FileResponse(path, media_type="application/json", filename=path.name)


__all__ = ["router"]
