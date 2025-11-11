"""Arena-specific API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..dependencies import get_current_user
from ..schemas import (
    ArenaMatchRequest,
    ArenaMatchResponse,
    ReplayParticipantSummary,
    ReplaySummary,
)
from ..services.match_runner import run_match
from ..services.storage import StorageManager

router = APIRouter(prefix="/arena", tags=["arena"])

storage = StorageManager()


def _replay_summary(replay: models.Replay) -> ReplaySummary:
    return ReplaySummary(
        id=replay.id,
        created_at=replay.created_at,
        winner_name=replay.winner_name,
        participants=[
            ReplayParticipantSummary(
                bot_label=participant.bot_label,
                placement=participant.placement,
                is_winner=participant.is_winner,
            )
            for participant in replay.participants
        ],
        summary=replay.summary,
    )


def _get_user_bot(db: Session, user: models.User, bot_id: int) -> models.Bot:
    bot = db.get(models.Bot, bot_id)
    if bot is None or bot.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    return bot


@router.post("/matches", response_model=ArenaMatchResponse)
def start_match(
    payload: ArenaMatchRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ArenaMatchResponse:
    bot = _get_user_bot(db, current_user, payload.bot_id)
    if not bot.current_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload a bot version before starting a match.",
        )

    result = run_match(db, bot.current_version, storage)

    replay_path = Path(result.replay.file_path)
    if not replay_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Replay file is missing on the server.",
        )

    with replay_path.open("r", encoding="utf-8") as handle:
        replay_data = json.load(handle)

    summary = _replay_summary(result.replay)
    return ArenaMatchResponse(replay=summary, replay_data=replay_data)


__all__ = ["router"]
