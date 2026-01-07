"""
Bot system package.

Contains:
- base: Abstract base class for all bots and Action types
- view: Safe, read-only game state view for bots
- loader: Dynamic bot loading from directory
"""

from game.bots.base import (
    Action,
    Bot,
    DefuseAction,
    DrawCardAction,
    GiveCardAction,
    PlayCardAction,
    PlayComboAction,
)
from game.bots.view import BotView
from game.bots.loader import BotLoader

__all__: list[str] = [
    # Bot interface
    "Bot",
    "BotView",
    "BotLoader",
    # Action types
    "Action",
    "DrawCardAction",
    "PlayCardAction",
    "PlayComboAction",
    "DefuseAction",
    "GiveCardAction",
]
