from dataclasses import dataclass

from card import CardCounts, Card


@dataclass
class GameState:
    total_cards_in_deck: CardCounts
    cards_left: int
    was_last_card_exploding_kitten: bool
    history_of_played_cards: list[Card]
