"""Utilities for running arena matches."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from game import GameEngine, ReplayRecorder

from .. import models
from .bot_loader import instantiate_bot
from .storage import StorageManager


@dataclass
class Participant:
    path: Path
    label: str
    bot_version_id: Optional[int]


class MatchResult:
    """Persisted replay metadata returned by a match run."""

    def __init__(self, replay: models.Replay):
        self.replay = replay


def _participant_from_version(version: models.BotVersion) -> Participant:
    if not version.file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bot version {version.id} has no associated file.",
        )
    path = Path(version.file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bot file {path} is missing on the server.",
        )
    bot = version.bot
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bot version {version.id} is not associated with a bot.",
        )
    label = bot.qualified_name
    return Participant(path=path, label=label, bot_version_id=version.id)


def select_opponents(db: Session, exclude_bot_id: int, limit: int) -> List[models.BotVersion]:
    opponents = (
        db.query(models.BotVersion)
        .join(models.Bot, models.Bot.id == models.BotVersion.bot_id)
        .filter(models.Bot.id != exclude_bot_id)
        .filter(models.Bot.current_version_id == models.BotVersion.id)
        .all()
    )
    random.shuffle(opponents)
    return opponents[:limit]


def run_match(db: Session, bot_version: models.BotVersion, storage: StorageManager) -> MatchResult:
    """Run a match for the provided bot version and persist the replay."""

    players: List[Participant] = [_participant_from_version(bot_version)]

    for version in select_opponents(db, bot_version.bot_id, limit=4):
        players.append(_participant_from_version(version))

    if len(players) < 2:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Not enough opponents available to run a match.",
        )

    instantiated = [
        instantiate_bot(p.path, f"arena_{idx}_{random.randint(1, 9999)}", p.label)
        for idx, p in enumerate(players)
    ]

    recorder = ReplayRecorder([bot.name for bot in instantiated], enabled=True)
    engine = GameEngine(instantiated, verbose=False, replay_recorder=recorder)
    winner = engine.play_game()

    replay_path = storage.new_replay_path()
    recorder.save_to_file(str(replay_path))

    placements = engine.get_placements()
    placement_map = {name: placement for name, placement in placements}

    replay = models.Replay(
        file_path=str(replay_path),
        winner_name=winner.name if winner else "No winner",
        summary={"placements": placements},
    )
    db.add(replay)
    db.flush()

    for participant in players:
        placement = placement_map.get(participant.label, len(players))
        is_winner = winner.name == participant.label if winner else False
        entry = models.ReplayParticipant(
            replay_id=replay.id,
            bot_version_id=participant.bot_version_id,
            bot_label=participant.label,
            placement=placement,
            is_winner=is_winner,
        )
        db.add(entry)

    db.flush()
    return MatchResult(replay=replay)


__all__ = ["run_match", "MatchResult"]
