from bot import Bot
from typing import List, Optional
from card import Card

class TimBot(Bot):
    def play(self, cards_left: int) -> Optional[Card]:
        # Implement bot logic here
        pass

    def handle_exploding_kitten(self) -> int:
        # Decide where to put the exploding kitten card
        return 0  # Put it on top of the deck

    def see_the_future(self, top_three: List[Card]):
        # Process the information about the top three cards
        pass