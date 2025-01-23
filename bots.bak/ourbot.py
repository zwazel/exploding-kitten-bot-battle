import random
from typing import List, Optional
import random
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class OurBot(Bot):
    def play(self, state: GameState) -> Optional[Card]:
        """
        This method is called when it's your turn to play.
        It strategically chooses a card to play based on the current game state.

        :param state: GameState object
        :return: Card object or None
        """
        # Prioritize survival and smart card usage
        if random.random() < 0.3:  # Small chance to skip playing a card
            return None

        # Filter out Defuse cards (we don't play these)
        playable_cards = [card for card in self.hand if card.card_type != CardType.DEFUSE]

        # Use "Attack" or "Skip" if you're at risk of drawing an Exploding Kitten
        if state.cards_left_to_draw < len(self.hand) / 2:  # Adjust risk based on deck size
            for card in playable_cards:
                if card.card_type in {CardType.ATTACK, CardType.SKIP}:
                    return card

        # Play "See the Future" to gain knowledge
        for card in playable_cards:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card

        # If no strategic card is available, play a random card
        if playable_cards:
            return random.choice(playable_cards)

        # Otherwise, do nothing
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Handles the placement of an Exploding Kitten after defusing it.
        Strategically places the Exploding Kitten to disadvantage opponents.

        :param state: GameState object
        :return: int index of the draw pile
        """
        # Safely get the number of players
        num_players = getattr(state, "players", None)
        if num_players is not None:
            num_players = len(num_players)  # Get the length if players exist
        else:
            num_players = 0  # Default to 0 players if not available

        # Place the Exploding Kitten near the top to target the next player
        if num_players > 2:
            return random.randint(0, min(3, state.cards_left_to_draw - 1))
        # Otherwise, place it randomly in a safe range
        return random.randint(0, state.cards_left_to_draw)

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        Uses information from "See the Future" to influence decisions.
        Logs the top three cards for strategic planning.

        :param state: GameState object
        :param top_three: List of top three cards of the draw pile
        :return: None
        """
        # If an Exploding Kitten is near the top, prepare by playing defensive cards
        for i, card in enumerate(top_three):
            if card.card_type == CardType.EXPLODING_KITTEN:
                # Log or remember the position of the Exploding Kitten
                self.next_kitten_index = i
                break
        else:
            self.next_kitten_index = None  # No Exploding Kitten seen
