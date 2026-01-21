"""
Safe, read-only view of the game state for bots.

This module provides the BotView class which exposes only the information
that a bot is allowed to see. This prevents cheating by ensuring bots
cannot access hidden information like other players' hands or the draw pile.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from game.cards.base import Card
    from game.history import GameEvent


class BotView:
    """
    A safe view of the game state for a specific bot.
    
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
    
    def __init__(
        self,
        my_id: str,
        my_hand: tuple[Card, ...],
        my_turns_remaining: int,
        discard_pile: tuple[Card, ...],
        draw_pile_count: int,
        other_players: tuple[str, ...],
        other_player_card_counts: dict[str, int],
        current_player: str,
        turn_order: tuple[str, ...],
        is_my_turn: bool,
        recent_events: tuple[GameEvent, ...],
        chat_queue: Any | None = None,
    ) -> None:
        """
        Initialize the bot view.
        
        Args:
            my_id: The ID of the bot this view is for.
            my_hand: The cards in this bot's hand.
            my_turns_remaining: Number of turns this bot must still take.
            discard_pile: All discarded cards.
            draw_pile_count: Number of cards in draw pile.
            other_players: IDs of other players still in the game.
            other_player_card_counts: Card counts for other players.
            current_player: ID of the player whose turn it is.
            turn_order: The order of play.
            is_my_turn: Whether it's currently this bot's turn.
            recent_events: Recent game events for context.
            chat_queue: Internal queue for chat messages (set by engine).
        """
        self.my_id: str = my_id
        self.my_hand: tuple[Card, ...] = my_hand
        self.my_turns_remaining: int = my_turns_remaining
        self.discard_pile: tuple[Card, ...] = discard_pile
        self.draw_pile_count: int = draw_pile_count
        self.other_players: tuple[str, ...] = other_players
        self.other_player_card_counts: dict[str, int] = other_player_card_counts
        self.current_player: str = current_player
        self.turn_order: tuple[str, ...] = turn_order
        self.is_my_turn: bool = is_my_turn
        self.recent_events: tuple[GameEvent, ...] = recent_events
        self._chat_queue: Any | None = chat_queue
    
    def say(self, message: str) -> None:
        """
        Send a chat message at any time.
        
        Use this to "talk" to other bots or add personality to your bot!
        Messages are visible to all players and recorded in game history.
        
        You can call say() in any bot method:
        - take_turn(): During your regular turn
        - react(): When reacting to another player's action (e.g., playing a Nope)
        - on_event(): When observing game events (e.g., responding to chat)
        - choose_defuse_position(): When handling an Exploding Kitten
        - choose_card_to_give(): When giving a card for Favor
        
        Args:
            message: The message to send (max 200 characters).
        
        Example:
            def react(self, view: BotView, event: GameEvent) -> Action | None:
                if self._should_nope(event):
                    view.say("Not so fast!")
                    return PlayCardAction(card=nope_card)
                return None
        
        Note:
            - Messages are truncated to 200 characters.
            - Chat messages appear in the log with [CHAT] prefix.
        """
        if self._chat_queue is not None:
            self._chat_queue.put((self.my_id, message))
    
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
