"""Exploding Kittens game engine and core components."""

from .cards import Card, CardType, ComboType, TargetContext
from .game_state import GameState
from .bot import Bot
from .deck import Deck
from .game_engine import GameEngine
from .config import (
    DEFAULT_DECK_CONFIG,
    get_deck_config,
    INITIAL_HAND_SIZE,
    INITIAL_DEFUSE_PER_PLAYER,
    MAX_TURNS_PER_GAME,
    CARDS_TO_SEE_IN_FUTURE,
)

__all__ = [
    'Card',
    'CardType',
    'ComboType',
    'TargetContext',
    'GameState',
    'Bot',
    'Deck',
    'GameEngine',
    'DEFAULT_DECK_CONFIG',
    'get_deck_config',
    'INITIAL_HAND_SIZE',
    'INITIAL_DEFUSE_PER_PLAYER',
    'MAX_TURNS_PER_GAME',
    'CARDS_TO_SEE_IN_FUTURE',
]
