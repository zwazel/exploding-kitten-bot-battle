"""
Game engine package for the bot battle card game.

This package contains:
- engine: Main game orchestrator
- state: Protected game state
- rng: Deterministic random number generator
- history: Event recording for replay
- turns: Turn and action management
- cards/: Card system
- bots/: Bot system
"""

from game.engine import GameEngine
from game.history import GameEvent, GameHistory
from game.rng import DeterministicRNG

__all__: list[str] = [
    "GameEngine",
    "GameEvent",
    "GameHistory",
    "DeterministicRNG",
]
