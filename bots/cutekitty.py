import random
from typing import Optional, List

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class CuteKittyBot(Bot):
    def __init__(self, name):
        super().__init__(name)
        self.immortal = False

    def play(self, state: GameState) -> Optional[Card]:
        normal_card = self._find_card(self.hand, CardType.NORMAL)
        skip_card = self._find_card(self.hand, CardType.SKIP)
        crystal_card = self._find_card(self.hand, CardType.SEE_THE_FUTURE)
        defuse_card = self._find_card(self.hand, CardType.DEFUSE)

        if normal_card is not None:  # Throw away all normal cards
            return self.hand[normal_card]

        if defuse_card is not None:  # I am immortal, so who cares
            return None

        if crystal_card is not None and not self.immortal:
            return self.hand[crystal_card]

        if skip_card is not None and not self.immortal:
            return self.hand[skip_card]

        self.immortal = False
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        return 0

    def see_the_future(self, state: GameState, top_three: List[Card]):
        if self._find_card(top_three, CardType.EXPLODING_KITTEN) is not None:
            self.immortal = False
        else:
            self.memento_mori = True

    def _find_card(self, stack: List[Card], card_type: CardType) -> Optional[Card]:
        # Get the first card of the given type in the stack
        for index, card in enumerate(stack):
            if card.card_type == card_type:
                return index
        return None
