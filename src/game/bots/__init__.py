"""
Bot system package.

Contains:
- base: Abstract base class for all bots
- view: Safe, read-only game state view for bots
- loader: Dynamic bot loading from directory
"""

from game.bots.base import Bot
from game.bots.view import BotView
from game.bots.loader import BotLoader

__all__: list[str] = [
    "Bot",
    "BotView",
    "BotLoader",
]
