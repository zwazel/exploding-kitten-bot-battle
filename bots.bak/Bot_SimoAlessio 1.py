import random
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class StrategicBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.future_cards: Optional[List[Card]] = None

    def play(self, state: GameState) -> Optional[Card]:
        """
        Decide which card to play on the bot's turn.
        """
        if self.future_cards:
            for card in self.future_cards:
                if card.card_type == CardType.EXPLODING_KITTEN:
                    for hand_card in self.hand:
                        if hand_card.card_type == CardType.SKIP:
                            return hand_card

        for card in self.hand:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card

        for card in self.hand:
            if card.card_type == CardType.SKIP:
                return card

        playable_cards = [card for card in self.hand if card.card_type != CardType.DEFUSE]
        if playable_cards:
            return random.choice(playable_cards)

        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Decide where to place the Exploding Kitten card when defusing.
        """
        if state.cards_left_to_draw == 1:
            return 0

        if self.future_cards:
            safe_index = len(self.future_cards)
            if safe_index < state.cards_left_to_draw:
                return safe_index

        return random.randint(0, state.cards_left_to_draw - 1)

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        Store the top three cards of the draw pile and adjust the bot's strategy.
        """
        self.future_cards = top_three

        for card in top_three:
            if card.card_type == CardType.EXPLODING_KITTEN:
                pass