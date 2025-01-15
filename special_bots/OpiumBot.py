import random
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState
import anthropic
from enum import Enum

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="",
)

messages = []


class ProbabilityOfNextExploding(Enum):
    DEFINITELY = 1.0
    PROBABLY = 0.5
    UNSURE = 0.3
    DEFINITELY_NOT = 0.0


system_prompt = """
You are a player of Exploding Kittens, and your goal is to win at all costs. You will analyze the current game situation and determine the best move to play. Based on the provided information, you should respond with the name of the card to play in lowercase, as a single word.

User will provide the following information: cards in hand, number of players remaining, known card positions (if any), whether an Exploding Kitten has been drawn, the number of cards left in the deck, the total cards in the deck,  the history of cards played, probability of next exploding(definitely: 1.0, probably: 0,5, unsure: 0.3, definitely_not: 0.0). Do not ask any further questions, just respond with your next move.

The cards you have available are: "see_future", "skip", "defuse", "normal", and "exploding kitten."

Game Rules:
- Each player starts with a hand of cards.
- Players take turns drawing cards from the deck.
- If a player draws an Exploding Kitten, they must use a Defuse card to avoid exploding. If they cannot, they are out of the game.
- Action cards like Skip and See the Future can be played to manipulate the game.
- The last player remaining wins.

Respond with the best move based on the current information.
"""


def send_message(prompt: str):
    prompt = {"role": "user", "content": prompt}
    messages.append(prompt)
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4096,
        system=system_prompt,
        messages=[prompt]
    )
    ai_message = {"role": "assistant", "content": message.content[0].text}
    messages.append(ai_message)
    return message


class OpiumBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.future_cards: List[Card] = []
        self.probability_of_next_exploding = [ProbabilityOfNextExploding.UNSURE]

    def play(self, state: GameState) -> Optional[Card]:

        known_probability_string = ""
        if len(self.probability_of_next_exploding) == 0:
            known_probability_string = "UNSURE"
        else:
            for probability in self.probability_of_next_exploding:
                known_probability_string += f"{probability.name}, "
        exploding_kittens_left = state.alive_bots - 1
        probability_of_exploding_next = exploding_kittens_left / state.cards_left_to_draw
        if len(self.probability_of_next_exploding) > 0:
            if self.probability_of_next_exploding[0] == ProbabilityOfNextExploding.DEFINITELY:
                probability_of_exploding_next = ProbabilityOfNextExploding.DEFINITELY.value
            elif self.probability_of_next_exploding[0] == ProbabilityOfNextExploding.DEFINITELY_NOT:
                probability_of_exploding_next = ProbabilityOfNextExploding.DEFINITELY_NOT.value

        skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
        defuse_cards = [card for card in self.hand if card.card_type == CardType.DEFUSE]
        see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
        normal_cards = [card for card in self.hand if card.card_type == CardType.NORMAL]
        if self.future_cards:
            ask_ai = {"hand": self.hand, "known_cards": self.future_cards, "players_left": state.alive_bots,
                      "kitten_drawn": state.was_last_card_exploding_kitten,
                      "draw_deck_amount": state.cards_left_to_draw, "total_amount": state.total_cards_in_deck,
                      "cards_played_history": str(state.history_of_played_cards),
                      "probability_of_exploding": str(probability_of_exploding_next)}
            response = send_message(str(ask_ai))
            response = response.content[0].text
        else:
            ask_ai = {"hand": self.hand, "players_left": state.alive_bots,
                      "kitten_drawn": state.was_last_card_exploding_kitten,
                      "draw_deck_amount": state.cards_left_to_draw}
            response = send_message(str(ask_ai))
            response = response.content[0].text

        if response == "skip" and skip_cards:
            print("H0MICIDE!!!!!")
            return skip_cards[0]
        elif response == "see_future" and see_the_future_cards:
            print("WHOLELOTTARED!")
            return see_the_future_cards[0]
        elif response == "defuse" and defuse_cards:
            print("SEEEEYUHH!")
            return defuse_cards[0]
        elif response == "normal" and normal_cards:
            print("FWAEHHHHH!!!")
            return normal_cards[0]

    def handle_exploding_kitten(self, state: GameState) -> int:
        return random.randint(0, 1)

    def see_the_future(self, state: GameState, top_three: List[Card]):
        self.future_cards = top_three
