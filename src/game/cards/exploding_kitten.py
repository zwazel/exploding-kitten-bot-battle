"""
Exploding Kitten and Defuse cards.

These are the core cards that drive the game's elimination mechanic:
- Exploding Kitten: Eliminates a player if drawn and not defused
- Defuse: Saves a player from an Exploding Kitten
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.cards.base import Card

if TYPE_CHECKING:
    from game.bots.view import BotView
    from game.engine import GameEngine


class ExplodingKittenCard(Card):
    """
    The Exploding Kitten card.
    
    When drawn, the player explodes and is eliminated from the game
    UNLESS they have a Defuse card to play. This card can never be
    played from hand - it only triggers when drawn.
    
    - Cannot be played voluntarily
    - Cannot be used as a reaction
    - Cannot be used in combos
    """
    
    @property
    def name(self) -> str:
        return "Exploding Kitten"
    
    @property
    def card_type(self) -> str:
        return "ExplodingKittenCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        # Exploding Kitten can never be played voluntarily
        return False
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def can_combo(self) -> bool:
        # Explicitly cannot be used in combos
        return False
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # This should never be called - the engine handles explosion
        pass


class DefuseCard(Card):
    """
    The Defuse card.
    
    When a player draws an Exploding Kitten and has a Defuse card,
    they can play it to avoid elimination. After defusing, the player
    secretly reinserts the Exploding Kitten anywhere in the draw pile.
    
    - Cannot be played voluntarily during normal turn
    - Only played in response to drawing an Exploding Kitten
    - Cannot be used as a reaction (to other players' actions)
    - Cannot be used in combos
    """
    
    @property
    def name(self) -> str:
        return "Defuse"
    
    @property
    def card_type(self) -> str:
        return "DefuseCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        # Defuse can only be played when responding to an Exploding Kitten
        # This is handled specially by the engine, not through normal play
        return False
    
    def can_play_as_reaction(self) -> bool:
        # Not a reaction to other players' actions
        return False
    
    def can_combo(self) -> bool:
        # Explicitly cannot be used in combos
        return False
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # The actual defuse logic is handled by the engine
        # This method is called after the defuse is confirmed
        engine.log(f"{player_id} defused the Exploding Kitten!")
