from enum import Enum
from typing import List, Optional
from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState

class ProbabilityOfNextExploding(Enum):
    DEFINITELY = 1.0
    PROBABLY = 0.75
    UNSURE = 0.5
    UNLIKELY = 0.25
    DEFINITELY_NOT = 0.0

class Bottler(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.future_probabilities = []  # Tracks probabilities for upcoming cards

    def play(self, state: GameState) -> Optional[Card]:
        # Update exploding kitten probability based on game state
        exploding_kittens_left = state.alive_bots - 1
        probability_of_exploding_next = exploding_kittens_left / state.cards_left_to_draw if state.cards_left_to_draw > 0 else 0.0

        # Adjust probability based on future insights
        if self.future_probabilities:
            probability_of_exploding_next = self.future_probabilities[0].value

        # Log decision-making information
        print(f"[{self.name}] Probability of drawing Exploding Kitten: {probability_of_exploding_next:.2f}")

        # Prioritize playing DEFUSE if it's the only way to avoid elimination
        if probability_of_exploding_next == ProbabilityOfNextExploding.DEFINITELY.value:
            defuse_cards = [card for card in self.hand if card.card_type == CardType.DEFUSE]
            if defuse_cards:
                print(f"[{self.name}] Playing DEFUSE to survive.")
                return defuse_cards[0]

        # Play a SEE_THE_FUTURE card if available to refine probabilities
        see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
        if see_the_future_cards:
            print(f"[{self.name}] Playing SEE_THE_FUTURE.")
            return see_the_future_cards[0]

        # Play a SKIP card if risk is too high
        if probability_of_exploding_next > ProbabilityOfNextExploding.UNLIKELY.value:
            skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
            if skip_cards:
                print(f"[{self.name}] Playing SKIP to avoid risk.")
                return skip_cards[0]

        # Play NORMAL cards if multiple DEFUSE cards are available
        defuse_cards = [card for card in self.hand if card.card_type == CardType.DEFUSE]
        if len(defuse_cards) > 1:
            normal_cards = [card for card in self.hand if card.card_type == CardType.NORMAL]
            if normal_cards:
                print(f"[{self.name}] Taking a calculated risk and playing NORMAL card.")
                return normal_cards[0]

        # Default to drawing a card if no other option
        print(f"[{self.name}] No safe play, drawing a card.")
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        # Strategically place Exploding Kitten near the bottom, but with some randomness
        position = max(1, state.cards_left_to_draw - 3)  # Ensure it's not always the same predictable spot
        print(f"[{self.name}] Placing Exploding Kitten at position {position}.")
        return position

    def see_the_future(self, state: GameState, top_three: List[Card]):
        # Analyze top three cards and update probabilities
        self.future_probabilities = []
        for card in top_three:
            if card.card_type == CardType.EXPLODING_KITTEN:
                self.future_probabilities.append(ProbabilityOfNextExploding.DEFINITELY)
            else:
                self.future_probabilities.append(ProbabilityOfNextExploding.DEFINITELY_NOT)

        # Log future card analysis
        top_three_types = [card.card_type.name for card in top_three]
        print(f"[{self.name}] Future cards: {', '.join(top_three_types)}")
        print(f"[{self.name}] Updated probabilities: {[p.name for p in self.future_probabilities]}")
