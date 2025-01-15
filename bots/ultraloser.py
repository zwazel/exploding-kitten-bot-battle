import random
from typing import List, Optional
from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState
from enum import Enum

class ProbabilityOfNextExploding(Enum):
    DEFINITELY = 1.0
    PROBABLY = 0.5
    UNSURE = 0.3
    DEFINITELY_NOT = 0.0

class ultraloser(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.last_see_the_future_turn = -3
        self.top_three = []
        self.current_turn = 0
        self.cards_played_this_turn = 0
        self.probability_of_next_exploding = [ProbabilityOfNextExploding.UNSURE]

    def play(self, state: GameState) -> Optional[Card]:
        # Update turn tracking
        self.current_turn += 1 if self.cards_played_this_turn == 0 else 0
        self.cards_played_this_turn = 0

        # Step 1: Use SEE_THE_FUTURE strategically
        see_the_future_cards = self.get_cards_by_type(CardType.SEE_THE_FUTURE)
        if see_the_future_cards and self.current_turn - self.last_see_the_future_turn > 2:
            self.last_see_the_future_turn = self.current_turn
            self.cards_played_this_turn += 1
            return see_the_future_cards[0]

        # Step 2: Calculate the probability of drawing an Exploding Kitten
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

        # Step 3: Handle the danger level
        if self._is_dangerous(state, probability_of_exploding_next):
            skip_cards = self.get_cards_by_type(CardType.SKIP)
            if skip_cards:
                self.cards_played_this_turn += 1
                return random.choice(skip_cards)

        # Step 4: Use SKIP or DEFUSE cards strategically
        skip_cards = self.get_cards_by_type(CardType.SKIP)
        defuse_cards = self.get_cards_by_type(CardType.DEFUSE)
        if probability_of_exploding_next > ProbabilityOfNextExploding.UNSURE.value and skip_cards:
            return skip_cards[0]

        if len(defuse_cards) > 1:
            normal_cards = self.get_cards_by_type(CardType.NORMAL)
            if normal_cards:
                return random.choice(normal_cards)

        # Step 5: Play normal cards if no high-risk situation
        normal_cards = self.get_cards_by_type(CardType.NORMAL)
        if normal_cards:
            self.cards_played_this_turn += 1
            return random.choice(normal_cards)

        # Step 6: Handle Exploding Kitten if we know its position
        if self.top_three:
            next_card = self.top_three.pop(0)
            if next_card.card_type == CardType.EXPLODING_KITTEN:
                if skip_cards:
                    self.cards_played_this_turn += 1
                    return skip_cards[0]

        # No cards to play, must draw
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        # Place Exploding Kitten strategically
        if self.top_three:
            safe_positions = [i for i, card in enumerate(self.top_three) if card.card_type != CardType.EXPLODING_KITTEN]
            if safe_positions:
                return safe_positions[0]
        return max(0, state.cards_left_to_draw - 2)

    def see_the_future(self, state: GameState, top_three: List[Card]):
        # Analyze SEE_THE_FUTURE results and adjust strategy
        self.top_three = top_three
        self.probability_of_next_exploding = []
        for card in top_three:
            if card.card_type == CardType.EXPLODING_KITTEN:
                self.probability_of_next_exploding.append(ProbabilityOfNextExploding.DEFINITELY)
            else:
                self.probability_of_next_exploding.append(ProbabilityOfNextExploding.DEFINITELY_NOT)

        print(f"I have this many probabilities of drawing an Exploding Kitten: {len(self.probability_of_next_exploding)}")

    def _is_dangerous(self, state: GameState, probability_of_exploding_next: float) -> bool:
        # Assess if the current situation is dangerous
        if probability_of_exploding_next > 0.2 or state.was_last_card_exploding_kitten:
            return True
        return state.cards_left_to_draw <= max(3, state.alive_bots)

    def get_cards_by_type(self, card_type: CardType) -> List[Card]:
        # Helper method to filter cards by type
        return [card for card in self.hand if card.card_type == card_type]
