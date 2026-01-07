"""
Cat cards for Exploding Kittens.

These cards have no effect when played alone, but can be used in combos:
- 2 of a kind: Steal a random card from a chosen player
- 3 of a kind: Name a card and steal it from a chosen player
- 5 different: Take any card from the discard pile

All cat cards can be played on your turn (does nothing alone).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.cards.base import Card

if TYPE_CHECKING:
    from game.bots.view import BotView
    from game.engine import GameEngine


class CatCard(Card):
    """
    Base class for all cat cards.
    
    Cat cards have no individual effect but can be used in combos.
    They can be played alone on your turn (does nothing).
    """
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        # Can be played on own turn (does nothing, but valid)
        return is_own_turn
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def can_combo(self) -> bool:
        return True
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # No effect when played alone - just note this
        engine.log("  (no effect when played alone)")


class TacoCatCard(CatCard):
    """Taco Cat - a palindromic feline."""
    
    @property
    def name(self) -> str:
        return "Taco Cat"
    
    @property
    def card_type(self) -> str:
        return "TacoCatCard"


class HairyPotatoCatCard(CatCard):
    """Hairy Potato Cat - a fuzzy spud."""
    
    @property
    def name(self) -> str:
        return "Hairy Potato Cat"
    
    @property
    def card_type(self) -> str:
        return "HairyPotatoCatCard"


class BeardCatCard(CatCard):
    """Beard Cat - a bearded feline."""
    
    @property
    def name(self) -> str:
        return "Beard Cat"
    
    @property
    def card_type(self) -> str:
        return "BeardCatCard"


class RainbowRalphingCatCard(CatCard):
    """Rainbow-Ralphing Cat - a colorful cat."""
    
    @property
    def name(self) -> str:
        return "Rainbow-Ralphing Cat"
    
    @property
    def card_type(self) -> str:
        return "RainbowRalphingCatCard"


class CattermelonCard(CatCard):
    """Cattermelon - half cat, half melon."""
    
    @property
    def name(self) -> str:
        return "Cattermelon"
    
    @property
    def card_type(self) -> str:
        return "CattermelonCard"
