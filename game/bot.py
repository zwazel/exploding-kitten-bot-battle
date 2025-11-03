"""Base Bot class that all bots must inherit from."""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from .cards import Card, CardType
from .game_state import GameState


class Bot(ABC):
    """
    Base class for all bots in the Exploding Kittens game.
    
    All bots must inherit from this class and implement the required methods.
    """

    def __init__(self, name: str):
        """
        Initialize the bot.
        
        Args:
            name: The name of the bot (typically the filename without .py extension)
        """
        self.name = name
        self.hand: List[Card] = []
        self.alive = True

    @abstractmethod
    def play(self, state: GameState) -> Optional[Card | List[Card]]:
        """
        Called when it's the bot's turn to play a card or combo.
        
        Args:
            state: The current game state
            
        Returns:
            A single card to play, a list of cards for a combo, or None to end the turn
        """
        pass

    @abstractmethod
    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Called when the bot draws an Exploding Kitten and has a Defuse card.
        
        Args:
            state: The current game state
            
        Returns:
            The index (0-based) in the draw pile where to insert the Exploding Kitten.
            0 means top of the deck, state.cards_left_to_draw means bottom.
        """
        pass

    @abstractmethod
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        Called when the bot plays a "See the Future" card.
        
        Args:
            state: The current game state
            top_three: The top three cards of the draw pile (index 0 is the top card)
        """
        pass
    
    @abstractmethod
    def choose_target(self, state: GameState, alive_players: List['Bot'], context: str) -> Optional['Bot']:
        """
        Called when bot needs to choose a target for Favor or combo.
        
        Args:
            state: The current game state
            alive_players: List of alive bots (excluding self)
            context: Why target is being chosen ("favor", "2-of-a-kind", "3-of-a-kind")
            
        Returns:
            The target bot, or None if no valid target
        """
        pass
    
    @abstractmethod
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        """
        Called when bot needs to give a card (for Favor).
        
        Args:
            state: The current game state
            
        Returns:
            The card to give from hand
        """
        pass
    
    @abstractmethod
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        """
        Called for 3-of-a-kind combo to request a specific card type.
        
        Args:
            state: The current game state
            
        Returns:
            The card type to request
        """
        pass
    
    @abstractmethod
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        """
        Called for 5-unique combo to pick a card from discard pile.
        
        Args:
            state: The current game state
            discard_pile: Cards in the discard pile
            
        Returns:
            The card to take from discard pile
        """
        pass
    
    def on_action_played(self, state: GameState, action_description: str, actor: 'Bot') -> None:
        """
        Called whenever ANY action happens in the game to notify the bot.
        This is for information tracking, not for response.
        
        Args:
            state: The current game state
            action_description: Description of the action being played
            actor: The bot who performed the action
        """
        # Default implementation does nothing. Bots can override to track game state.
        pass
    
    @abstractmethod
    def should_play_nope(self, state: GameState, action_description: str) -> bool:
        """
        Called when an action can be noped. Bot decides whether to play a Nope card.
        
        Args:
            state: The current game state
            action_description: Description of the action being played
            
        Returns:
            True if bot wants to play Nope, False otherwise
        """
        pass

    def has_card(self, card: Card) -> bool:
        """Check if the bot has a specific card in hand."""
        return card in self.hand

    def has_card_type(self, card_type) -> bool:
        """Check if the bot has any card of a specific type."""
        return any(card.card_type == card_type for card in self.hand)

    def remove_card(self, card: Card) -> bool:
        """
        Remove a card from the bot's hand.
        
        Args:
            card: The card to remove
            
        Returns:
            True if the card was removed, False if it wasn't in the hand
        """
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False

    def add_card(self, card: Card) -> None:
        """Add a card to the bot's hand."""
        self.hand.append(card)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Bot({self.name})"
