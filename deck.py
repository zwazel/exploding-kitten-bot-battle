""" Provides the Deck class, which represents the deck of cards in the game. """
import random
from typing import List

from bot import Bot
from card import Card, CardType, CardCounts


class Deck:
    """
    Represents the deck of cards in the game.
    0 is the top of the deck, len(deck) - 1 is the bottom of the deck. So drawing a card is deck.pop(0).
    """

    def __init__(self, card_counts: CardCounts, amount_players: int) -> None:
        """
        Constructor for the Deck class
        :param card_counts: CardCounts object
        :param amount_players: int number of players in the game
        :return: None
        """
        self._cards: List[Card] = []
        self._discard_pile: List[Card] = []
        self.initialize_deck(card_counts, amount_players)

    def initialize_deck(self, card_counts: CardCounts, amount_players: int) -> None:
        """
        Initializes the deck with the given card counts
        :param card_counts: CardCounts object
        :param amount_players: int number of players in the game
        :return: None
        """
        self.cards = []
        for card_type in CardType:
            if card_type == CardType.EXPLODING_KITTEN:
                continue
            count = getattr(card_counts, card_type.name)
            if card_type == CardType.DEFUSE:
                # 1 Defuse card is given to each player at the start of the game
                count -= amount_players
            self.cards.extend([Card(card_type) for _ in range(count)])
        random.shuffle(self.cards)

    def initialize_bot_hands(self, bots: List[Bot], card_counts: CardCounts) -> None:
        """
        Initializes the bots' hands
        :param bots: List of Bot objects
        :param card_counts: CardCounts object
        :return: None
        """
        for bot in bots:
            print(f'Initializing hand for {bot.name}')
            bot.add_card(Card(CardType.DEFUSE))

            while len(bot.hand) <= 5:
                card = self.draw()
                bot.add_card(card)

            print(f'{bot.name} has the following cards:')
            card_string = ''
            for card in bot.hand:
                card_string += card.card_type.name + ', '
            print(card_string[:-2])
            print()

        # add exploding kittens
        for _ in range(card_counts.EXPLODING_KITTEN):
            self.insert_exploding_kitten(random.randint(0, len(self.cards)))

        random.shuffle(self.cards)

        print('Exploding kittens added to deck')
        print('Deck: ')
        deck_string = ''
        for card in self.cards:
            deck_string += card.card_type.name + ', '
        print(deck_string[:-2])
        print()

    def draw(self) -> Card:
        """
        Draws a card from the deck
        :return: Card object
        """
        if not self.cards:
            raise ValueError('Deck is empty')
        return self.cards.pop(0)

    def insert_exploding_kitten(self, index: int) -> None:
        """
        Inserts an exploding kitten card at the given index
        :param index: int index to insert the card at
        :return: None
        """
        if index < 0:
            index = 0
        elif index > len(self.cards):
            index = len(self.cards)
        self.cards.insert(index, Card(CardType.EXPLODING_KITTEN))

    def discard(self, card: Card) -> None:
        """
        Discards a card to the discard pile
        :param card: Card object
        :return: None
        """
        self.discard_pile.append(card)

    def peek(self, count: int) -> List[Card]:
        """
        Peeks at the top count cards of the deck
        :param count: int number of cards to peek at
        :return: List of Card objects
        """
        return self.cards[:count]

    def cards_left(self) -> int:
        """
        Returns the number of cards left in the deck
        :return: int
        """
        return len(self.cards)

    @property
    def cards(self):
        """ returns the cards """
        return self._cards

    @cards.setter
    def cards(self, value):
        """ sets the cards """
        self._cards = value

    @property
    def discard_pile(self):
        """ returns the discard_pile """
        return self._discard_pile

    @discard_pile.setter
    def discard_pile(self, value):
        """ sets the discard_pile """
        self._discard_pile = value
