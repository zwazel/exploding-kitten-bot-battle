"""Deck management for Exploding Kittens game."""

import random
from typing import List
from .cards import Card, CardType
from .game_state import CardCounts


class Deck:
    """Manages the draw pile and discard pile for the game."""

    def __init__(self, num_players: int):
        """
        Initialize the deck for a game.
        
        Args:
            num_players: Number of players in the game
        """
        self.draw_pile: List[Card] = []
        self.discard_pile: List[Card] = []
        self._initialize_deck(num_players)

    def _initialize_deck(self, num_players: int) -> None:
        """
        Create and shuffle the initial deck.
        
        Standard Exploding Kittens deck composition:
        - Exploding Kittens: num_players - 1 (inserted after initial deal)
        - Defuse cards: 6 total (1 dealt to each player, rest in deck)
        - Skip: 4
        - See the Future: 5
        - Shuffle: 4
        - Favor: 4
        - Attack: 4
        - Nope: 5
        - Cat cards: 4 of each type (Tacocat, Cattermelon, Hairy Potato Cat, Beard Cat, Rainbow-Ralphing Cat)
        """
        cards = []
        
        # Add Defuse cards (will be distributed to players and deck)
        for _ in range(6):
            cards.append(Card(CardType.DEFUSE))
        
        # Add action cards
        for _ in range(4):
            cards.append(Card(CardType.SKIP))
        for _ in range(5):
            cards.append(Card(CardType.SEE_THE_FUTURE))
        for _ in range(4):
            cards.append(Card(CardType.SHUFFLE))
        for _ in range(4):
            cards.append(Card(CardType.FAVOR))
        for _ in range(4):
            cards.append(Card(CardType.ATTACK))
        for _ in range(5):
            cards.append(Card(CardType.NOPE))
        
        # Add cat cards (4 of each type)
        for _ in range(4):
            cards.append(Card(CardType.TACOCAT))
        for _ in range(4):
            cards.append(Card(CardType.CATTERMELON))
        for _ in range(4):
            cards.append(Card(CardType.HAIRY_POTATO_CAT))
        for _ in range(4):
            cards.append(Card(CardType.BEARD_CAT))
        for _ in range(4):
            cards.append(Card(CardType.RAINBOW_RALPHING_CAT))

        # Shuffle the deck
        random.shuffle(cards)
        
        self.draw_pile = cards
        # Exploding Kittens will be added after initial deal

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

    def get_total_card_counts(self) -> CardCounts:
        """
        Count all cards that were in the initial deck.
        
        Returns:
            CardCounts object with the total count of each card type
        """
        counts = CardCounts()
        all_cards = self.draw_pile + self.discard_pile
        
        for card in all_cards:
            if card.card_type == CardType.EXPLODING_KITTEN:
                counts.exploding_kitten += 1
            elif card.card_type == CardType.DEFUSE:
                counts.defuse += 1
            elif card.card_type == CardType.SKIP:
                counts.skip += 1
            elif card.card_type == CardType.SEE_THE_FUTURE:
                counts.see_the_future += 1
            elif card.card_type == CardType.SHUFFLE:
                counts.shuffle += 1
            elif card.card_type == CardType.FAVOR:
                counts.favor += 1
            elif card.card_type == CardType.ATTACK:
                counts.attack += 1
            elif card.card_type == CardType.NOPE:
                counts.nope += 1
            elif card.card_type == CardType.TACOCAT:
                counts.tacocat += 1
            elif card.card_type == CardType.CATTERMELON:
                counts.cattermelon += 1
            elif card.card_type == CardType.HAIRY_POTATO_CAT:
                counts.hairy_potato_cat += 1
            elif card.card_type == CardType.BEARD_CAT:
                counts.beard_cat += 1
            elif card.card_type == CardType.RAINBOW_RALPHING_CAT:
                counts.rainbow_ralphing_cat += 1
        
        return counts
