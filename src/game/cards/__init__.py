"""
Card system package.

Contains:
- base: Abstract base class for all cards
- registry: Card type registration and deck creation
- placeholder: Test/placeholder cards for development
"""

from game.cards.base import Card
from game.cards.registry import CardRegistry

__all__: list[str] = [
    "Card",
    "CardRegistry",
]
