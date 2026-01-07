"""
Placeholder cards for testing and development.

These cards demonstrate the card system and can be used for testing
before implementing the actual game cards.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.cards.base import Card

if TYPE_CHECKING:
    from game.bots.view import BotView
    from game.engine import GameEngine


class DrawCard(Card):
    """
    A placeholder card that forces the player to draw extra cards.
    
    Effect: Draw 2 cards from the draw pile.
    Can only be played on own turn.
    Cannot be played as a reaction.
    """
    
    @property
    def name(self) -> str:
        return "Draw"
    
    @property
    def card_type(self) -> str:
        return "DrawCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        return is_own_turn
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # Draw 2 cards
        engine.draw_cards(player_id, count=2)


class SkipCard(Card):
    """
    A placeholder card that skips the current turn.
    
    Effect: End the turn without drawing a card.
    Can only be played on own turn.
    Cannot be played as a reaction.
    """
    
    @property
    def name(self) -> str:
        return "Skip"
    
    @property
    def card_type(self) -> str:
        return "SkipCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        return is_own_turn
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # Skip this turn - reduce turns remaining
        engine.skip_turn(player_id)


class NopeCard(Card):
    """
    A placeholder reaction card that cancels another card's effect.
    
    Effect: Cancel the effect of the card being played.
    CAN be played out of turn as a reaction.
    """
    
    @property
    def name(self) -> str:
        return "Nope"
    
    @property
    def card_type(self) -> str:
        return "NopeCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        # Nope can only be played as a reaction, not proactively
        return False
    
    def can_play_as_reaction(self) -> bool:
        return True
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # The nope effect is handled by the engine's reaction system
        # This just records that the nope was played
        engine.log(f"Player {player_id} played Nope!")


class AttackCard(Card):
    """
    A placeholder card that adds extra turns to the next player.
    
    Effect: End your turn and force the next player to take 2 turns.
    Can only be played on own turn.
    Cannot be played as a reaction.
    """
    
    @property
    def name(self) -> str:
        return "Attack"
    
    @property
    def card_type(self) -> str:
        return "AttackCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        return is_own_turn
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # End current player's turn and give next player 2 turns
        engine.attack_next_player(player_id, extra_turns=2)


class ComboCard(Card):
    """
    A placeholder card that can be used in combos.
    
    Cannot be played individually - only as part of a combo.
    Combo effects are handled by the engine based on the pattern:
    - 2 of a kind: steal random card from chosen player
    - 3 of a kind: name and steal specific card
    - 5 different: draw from discard pile
    """
    
    @property
    def name(self) -> str:
        return "Combo"
    
    @property
    def card_type(self) -> str:
        return "ComboCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        # Can only be played as part of a combo
        return False
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def can_combo(self) -> bool:
        return True
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # Should not be played individually
        pass


# Register all placeholder cards with the default registry
def register_placeholder_cards(registry: "CardRegistry") -> None:
    """
    Register all placeholder cards with a registry.
    
    Args:
        registry: The card registry to register with.
    """
    from game.cards.registry import CardRegistry
    
    registry.register_with_type("DrawCard", DrawCard)
    registry.register_with_type("SkipCard", SkipCard)
    registry.register_with_type("NopeCard", NopeCard)
    registry.register_with_type("AttackCard", AttackCard)
    registry.register_with_type("ComboCard", ComboCard)
