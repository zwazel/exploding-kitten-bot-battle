"""
Safe, read-only view of the game state for bots.

This module provides the BotView class which exposes only the information
that a bot is allowed to see. This prevents cheating by ensuring bots
cannot access hidden information like other players' hands or the draw pile.
"""

from __future__ import annotations

import queue
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from game.cards.base import Card
    from game.history import GameEvent


class ChatProxy:
    """
    A secure, write-only proxy for the chat queue.
    
    This class prevents bots from:
    - Directly accessing the underlying queue
    - Spoofing player IDs in messages
    - Draining or manipulating the queue
    
    Bots can only send messages through the `send()` method.
    """
    
    __slots__ = ('_queue', '_player_id', '_max_length')
    
    def __init__(self, q: queue.Queue[tuple[str, str]], player_id: str, max_length: int = 200) -> None:
        """
        Initialize the chat proxy.
        
        Args:
            q: The underlying queue to send messages to.
            player_id: The ID of the player this proxy is for (cannot be changed).
            max_length: Maximum message length (truncated if longer).
        """
        object.__setattr__(self, '_queue', q)
        object.__setattr__(self, '_player_id', player_id)
        object.__setattr__(self, '_max_length', max_length)
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Prevent modification of proxy attributes."""
        raise AttributeError("ChatProxy is read-only")
    
    def __delattr__(self, name: str) -> None:
        """Prevent deletion of proxy attributes."""
        raise AttributeError("ChatProxy is read-only")
    
    def send(self, message: str) -> None:
        """
        Send a chat message.
        
        Args:
            message: The message to send (will be truncated to max_length).
        """
        if not isinstance(message, str):
            return  # Silently ignore non-string messages
        
        # Truncate message to prevent spam
        truncated = message[:self._max_length] if message else ""
        if truncated:
            self._queue.put((self._player_id, truncated))


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
        chat_proxy: ChatProxy | None = None,
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
            chat_proxy: Secure proxy for sending chat messages.
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
        self._chat_proxy: ChatProxy | None = chat_proxy
    
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
        if self._chat_proxy is not None:
            self._chat_proxy.send(message)
    
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
