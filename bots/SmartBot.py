from enum import Enum
from typing import List, Optional
from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState

"""
Design flaw: 
- he correctly remembers the next 3 cards, and he then assumes that all 3 next cards that he draws are these 3.
- but other bots draw them too. so they aren't even in there anymore. stupid.
"""
class ProbabilityOfNextExploding(Enum):
    DEFINITELY = 1.0
    PROBABLY = 0.5
    UNSURE = 0.3
    DEFINITELY_NOT = 0.0

class SmartBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.probability_of_next_exploding = [ProbabilityOfNextExploding.UNSURE]

    def play(self, state: GameState) -> Optional[Card]:
        # Calculate the probability of drawing an Exploding Kitten
        known_probability_string = ""
        if len(self.probability_of_next_exploding) == 0:
            known_probability_string = "UNSURE"
        else:
            for probability in self.probability_of_next_exploding:
                known_probability_string += f"{probability.name}, "
        print(f"My known probability of drawing an Exploding Kitten is {known_probability_string}")
        exploding_kittens_left = state.alive_bots - 1
        probability_of_exploding_next = exploding_kittens_left / state.cards_left_to_draw
        if len(self.probability_of_next_exploding) > 0:
            if self.probability_of_next_exploding[0] == ProbabilityOfNextExploding.DEFINITELY:
                probability_of_exploding_next = ProbabilityOfNextExploding.DEFINITELY.value
            elif self.probability_of_next_exploding[0] == ProbabilityOfNextExploding.DEFINITELY_NOT:
                probability_of_exploding_next = ProbabilityOfNextExploding.DEFINITELY_NOT.value

        # If we have a SEE_THE_FUTURE card, use it before deciding to play a SKIP card
        if probability_of_exploding_next > ProbabilityOfNextExploding.DEFINITELY_NOT.value:
            see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
            if see_the_future_cards:
                return see_the_future_cards[0]

        # If the probability of drawing an Exploding Kitten is too high, play a SKIP card
        skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
        if probability_of_exploding_next > ProbabilityOfNextExploding.UNSURE.value and skip_cards:
            return skip_cards[0]

        # If we have multiple DEFUSE cards, we can take more risks
        defuse_cards = [card for card in self.hand if card.card_type == CardType.DEFUSE]
        if len(defuse_cards) > 1:
            # Play a normal card if we have multiple DEFUSE cards
            normal_cards = [card for card in self.hand if card.card_type == CardType.NORMAL]
            if normal_cards:
                return normal_cards[0]

        if len(self.probability_of_next_exploding) <= 0:
            self.probability_of_next_exploding = [ProbabilityOfNextExploding.UNSURE]
        else:
            self.probability_of_next_exploding.pop(0)

        # If no other cards to play, return None to draw a card
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        # Place the Exploding Kitten near the bottom of the deck
        return max(0, state.cards_left_to_draw - 2)

    def see_the_future(self, state: GameState, top_three: List[Card]):
        self.probability_of_next_exploding = []
        for card in top_three:
            if card.card_type == CardType.EXPLODING_KITTEN:
                self.probability_of_next_exploding.append(ProbabilityOfNextExploding.DEFINITELY)
            else:
                self.probability_of_next_exploding.append(ProbabilityOfNextExploding.DEFINITELY_NOT)