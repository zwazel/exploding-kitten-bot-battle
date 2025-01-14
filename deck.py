from typing import List, Dict
import random
from card import Card, CardType, CardCounts

class Deck:
    def __init__(self, card_counts: CardCounts):
        self.draw_pile: List[Card] = []
        self.discard_pile: List[Card] = []
        self.card_counts = card_counts

    def initialize(self, num_players: int):
        self.draw_pile = []
        for card_type in CardType:
            count = getattr(self.card_counts, card_type.name)
            if card_type == CardType.EXPLODING_KITTEN:
                count = num_players - 1
            self.draw_pile.extend([Card(card_type) for _ in range(count)])
        random.shuffle(self.draw_pile)

    def draw(self) -> Card:
        if not self.draw_pile:
            self.draw_pile = self.discard_pile
            self.discard_pile = []
            random.shuffle(self.draw_pile)
        return self.draw_pile.pop()

    def discard(self, card: Card):
        self.discard_pile.append(card)

    def insert_exploding_kitten(self, index: int):
        self.draw_pile.insert(index, Card(CardType.EXPLODING_KITTEN))

    def peek(self, num_cards: int) -> List[Card]:
        return self.draw_pile[:num_cards]

    def cards_left(self) -> int:
        return len(self.draw_pile)