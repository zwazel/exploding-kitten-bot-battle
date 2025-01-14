import random
from typing import List

from bot import Bot
from card import Card, CardType, CardCounts


class Deck:
    """
    Represents the deck of cards in the game.
    0 is the top of the deck, len(deck) - 1 is the bottom of the deck. So drawing a card is deck.pop(0).
    """
    def __init__(self, card_counts: CardCounts, amount_players: int):
        self.cards: List[Card] = []
        self.discard_pile: List[Card] = []
        self.initialize_deck(card_counts, amount_players)

    def initialize_deck(self, card_counts: CardCounts, amount_players: int):
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

    def initialize_bot_hands(self, bots: List[Bot], card_counts: CardCounts):
        for bot in bots:
            print(f"Initializing hand for {bot.name}")
            bot.add_card(Card(CardType.DEFUSE))

            while len(bot.hand) <= 5:
                card = self.draw()
                bot.add_card(card)

            print(f"{bot.name} has the following cards:")
            card_string = ""
            for card in bot.hand:
                card_string += card.card_type.name + ", "
            print(card_string[:-2])
            print()

        # add exploding kittens
        for _ in range(card_counts.EXPLODING_KITTEN):
            self.insert_exploding_kitten(random.randint(0, len(self.cards)))

        random.shuffle(self.cards)

        print("Exploding kittens added to deck")
        print("Deck: ")
        deck_string = ""
        for card in self.cards:
            deck_string += card.card_type.name + ", "
        print(deck_string[:-2])
        print()

    def draw(self) -> Card:
        if not self.cards:
            raise ValueError("Deck is empty")
        return self.cards.pop(0)

    def insert_exploding_kitten(self, index: int):
        if index < 0:
            index = 0
        elif index > len(self.cards):
            index = len(self.cards)
        self.cards.insert(index, Card(CardType.EXPLODING_KITTEN))

    def discard(self, card: Card):
        self.discard_pile.append(card)

    def peek(self, count: int) -> List[Card]:
        return self.cards[:count]

    def cards_left(self) -> int:
        return len(self.cards)