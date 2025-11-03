"""Deck management for Exploding Kittens game."""

import random
from typing import List, Dict
from .cards import Card, CardType
from .config import get_deck_config


class Deck:
    """Manages the draw pile and discard pile for the game."""

    def __init__(self, num_players: int, custom_config: Dict[CardType, int] = None):
        """
        Initialize the deck for a game.
        
        Args:
            num_players: Number of players in the game
            custom_config: Optional custom card counts to override defaults
        """
        self.draw_pile: List[Card] = []
        self.discard_pile: List[Card] = []
        self.config = get_deck_config(custom_config)
        self.num_players = num_players
        self._initialize_deck()

    def _initialize_deck(self) -> None:
        """
        Create and shuffle the initial deck based on configuration.
        
        Exploding Kittens are added separately: num_players - 1 (inserted after initial deal)
        """
        cards = []
        
        # Add cards based on configuration
        for card_type, count in self.config.items():
            for _ in range(count):
                cards.append(Card(card_type))

        # Shuffle the deck
        random.shuffle(cards)
        
        self.draw_pile = cards
        # Exploding Kittens will be added after initial deal

    def get_initial_card_counts(self) -> Dict[CardType, int]:
        """
        Get the initial card counts that were used to create the deck.
        This includes Exploding Kittens that will be added.
        
        Returns:
            Dictionary mapping CardType to initial count
        """
        counts = self.config.copy()
        # Add Exploding Kittens count (num_players - 1)
        counts[CardType.EXPLODING_KITTEN] = self.num_players - 1
        return counts

    def shuffle(self) -> None:
        """Shuffle the draw pile."""
        random.shuffle(self.draw_pile)

    def draw(self) -> Card:
        """
        Draw a card from the top of the draw pile.
        
        Returns:
            The card drawn
            
        Raises:
            IndexError: If the draw pile is empty
        """
        if not self.draw_pile:
            raise IndexError("Cannot draw from empty deck")
        return self.draw_pile.pop(0)

    def insert_at(self, card: Card, position: int) -> None:
        """
        Insert a card at a specific position in the draw pile.
        
        Args:
            card: The card to insert
            position: The position to insert at (0 = top of deck)
        """
        # Clamp position to valid range
        position = max(0, min(position, len(self.draw_pile)))
        self.draw_pile.insert(position, card)

    def add_to_bottom(self, card: Card) -> None:
        """Add a card to the bottom of the draw pile."""
        self.draw_pile.append(card)

    def add_to_top(self, card: Card) -> None:
        """Add a card to the top of the draw pile."""
        self.draw_pile.insert(0, card)

    def peek(self, count: int = 1) -> List[Card]:
        """
        Peek at the top cards of the draw pile without removing them.
        
        Args:
            count: Number of cards to peek at
            
        Returns:
            List of cards (up to count cards)
        """
        return self.draw_pile[:min(count, len(self.draw_pile))]

    def size(self) -> int:
        """Get the number of cards in the draw pile."""
        return len(self.draw_pile)
