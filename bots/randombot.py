import random
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class RandomBot(Bot):
    def play(self, state: GameState) -> Optional[Card]:
        """
        This method is called when it's my turn to play
        I return a random card or None

        :param state: GameState object
        :return: Card object or None
        """
        if random.random() < 0.5:
            return None
        playable_cards = [card for card in self.hand if card.card_type != CardType.DEFUSE]
        if playable_cards:
            return random.choice(playable_cards)
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        I drew an exploding kitten card and had a defuse card in my hand
        I put the exploding kitten card at a random spot in the draw pile
        :param state: GameState object
        :return: int  index of the draw pile
        """
        return random.randint(0, state.cards_left_to_draw)

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        This method is called after I played a "See the future" card
        I do nothing
        :param state: GameState object
        :param top_three: List of top three cards of the draw pile
        :return: None
        """
        pass

    def card_played(self, card_type: CardType, position: int) -> bool:
        """
        This method is called when another bot plays a card
        I do nothing
        :param card_type: CardType object
        :param position: int
        :return: bool
        """
        return True