"""
Safe, read-only view of the game state for bots.

This module provides the BotView class which exposes only the information
that a bot is allowed to see. This prevents cheating by ensuring bots
cannot access hidden information like other players' hands or the draw pile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.cards.base import Card
    from game.history import GameEvent


@dataclass(frozen=True)
class BotView:
    """
    An immutable, safe view of the game state for a specific bot.
    
    This is what bots receive instead of the full GameState. It only
    contains information the bot is allowed to see.
    
    All collections are tuples (immutable) to prevent modification.
    
    Attributes:
        my_id: The ID of the bot this view is for.
        my_hand: The cards in this bot's hand (immutable).
        my_turns_remaining: Number of turns this bot must still take.
        discard_pile: All discarded cards (visible to everyone).
        draw_pile_count: Number of cards in draw pile (NOT contents!).
        other_players: IDs of other players still in the game.
        other_player_card_counts: Card counts for other players.
        current_player: ID of the player whose turn it is.
        turn_order: The order of play (player IDs).
        is_my_turn: Whether it's currently this bot's turn.
        recent_events: Recent game events for context.
    """
    
    my_id: str
    my_hand: tuple[Card, ...]
    my_turns_remaining: int
    discard_pile: tuple[Card, ...]
    draw_pile_count: int
    other_players: tuple[str, ...]
    other_player_card_counts: dict[str, int]
    current_player: str
    turn_order: tuple[str, ...]
    is_my_turn: bool
    recent_events: tuple[GameEvent, ...]
    
    def get_cards_of_type(self, card_type: str) -> tuple[Card, ...]:
        """
        Get all cards of a specific type from own hand.
        
        Args:
            card_type: The card type to filter for.
            
        Returns:
            Tuple of matching cards.
        """
        return tuple(c for c in self.my_hand if c.card_type == card_type)
    
    def has_card_type(self, card_type: str) -> bool:
        """
        Check if the bot has at least one card of a type.
        
        Args:
            card_type: The card type to check for.
            
        Returns:
            True if the bot has at least one card of this type.
        """
        return any(c.card_type == card_type for c in self.my_hand)
    
    def count_cards_of_type(self, card_type: str) -> int:
        """
        Count how many cards of a type the bot has.
        
        Args:
            card_type: The card type to count.
            
        Returns:
            Number of cards of this type in hand.
        """
        return sum(1 for c in self.my_hand if c.card_type == card_type)
    
    def get_playable_cards(self) -> tuple[Card, ...]:
        """
        Get all cards that can currently be played.
        
        Returns:
            Tuple of cards that can be played.
        """
        return tuple(c for c in self.my_hand if c.can_play(self, self.is_my_turn))
    
    def get_reaction_cards(self) -> tuple[Card, ...]:
        """
        Get all cards that can be played as reactions.
        
        Returns:
            Tuple of cards that can be played as reactions.
        """
        return tuple(c for c in self.my_hand if c.can_play_as_reaction())
    
    def can_play_combo(self, card_type: str, required_count: int = 2) -> bool:
        """
        Check if the bot can play a combo of a specific card type.
        
        Args:
            card_type: The card type to check for.
            required_count: Minimum number needed for a combo.
            
        Returns:
            True if a combo can be played.
        """
        matching: tuple[Card, ...] = self.get_cards_of_type(card_type)
        if len(matching) < required_count:
            return False
        return all(c.can_combo() for c in matching[:required_count])
