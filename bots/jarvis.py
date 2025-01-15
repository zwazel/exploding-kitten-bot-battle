import random
from typing import List, Optional
from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class Jarvis(Bot):
    def play(self, state: GameState) -> Optional[Card]:
        """
        Decide which card to play based on game state and card priorities.
        """
        # Step 1: Prioritize SEE THE FUTURE cards
        see_the_future_cards = self._get_cards_of_type(CardType.SEE_THE_FUTURE)
        if see_the_future_cards:
            return see_the_future_cards[0]

        # Step 2: Use SKIP cards if danger is imminent
        if self._is_threatening(state):
            return self._play_skip_card()

        # Step 3: Play NORMAL cards to delay drawing if nothing critical is needed
        normal_cards = self._get_cards_of_type(CardType.NORMAL)
        if normal_cards:
            return random.choice(normal_cards)

        # Step 4: If no cards to play, draw a card and hope for the best
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Decide where to place the Exploding Kitten in the deck.
        """
        position = self._calculate_exploding_kitten_position(state)
        print(f"Placing Exploding Kitten back into position {position} of the deck.")
        return position

    def see_the_future(self, state: GameState, top_three: List[Card]) -> Optional[Card]:
        """
        Analyze the top three cards revealed by SEE THE FUTURE and adjust strategy.
        """
        danger_positions = self._find_exploding_kitten_positions(top_three)

        # Handle immediate danger
        if danger_positions:
            if danger_positions[0] == 0:
                return self._handle_imminent_danger()

            self._prepare_for_future_danger()

        # If safe, return None to take no action
        return None

    # ------------------------------------------
    # Helper Methods for Structure Clarity
    # ------------------------------------------

    def _get_cards_of_type(self, card_type: CardType) -> List[Card]:
        """
        Retrieve all cards of a given type from the bot's hand.
        """
        return [card for card in self.hand if card.card_type == card_type]

    def _is_threatening(self, state: GameState) -> bool:
        """
        Assess if the current situation is dangerous based on game state.
        """
        return state.was_last_card_exploding_kitten or state.cards_left <= max(3, state.alive_bots)

    def _play_skip_card(self) -> Optional[Card]:
        """
        Play a SKIP card to avoid danger.
        """
        skip_cards = self._get_cards_of_type(CardType.SKIP)
        if skip_cards:
            return random.choice(skip_cards)
        return None

    def _find_exploding_kitten_positions(self, top_three: List[Card]) -> List[int]:
        """
        Identify the positions of any Exploding Kittens in the top three cards.
        """
        return [i for i, card in enumerate(top_three) if card.card_type == CardType.EXPLODING_KITTEN]

    def _handle_imminent_danger(self) -> Optional[Card]:
        """
        Handle the scenario where an Exploding Kitten is imminent and SKIP should be used.
        """
        skip_cards = self._get_cards_of_type(CardType.SKIP)
        if skip_cards:
            print("Using SKIP to avoid imminent Exploding Kitten.")
            return skip_cards[0]
        return None

    def _prepare_for_future_danger(self) -> None:
        """
        Prepare for future danger when Exploding Kittens are detected.
        """
        print("Danger is near, preparing to avoid it in the next turns.")

    def _calculate_exploding_kitten_position(self, state: GameState) -> int:
        """
        Calculate the optimal position for the Exploding Kitten based on the deck and players.
        """
        if state.cards_left > state.alive_bots:
            return state.cards_left // state.alive_bots
        return random.randint(0, state.cards_left - 1)

    def place_exploding_kitten(self, state: GameState) -> int:
        """
        Always place the Exploding Kitten in a position that maximizes the chance for the other players
        to draw and explode.
        """
        # Maximize the chance for other players to hit the Exploding Kitten
        # Ideally place the Exploding Kitten near the end of the deck, after the bot's turn
        # to ensure other players are more likely to draw it.

        # If there are many cards, place it closer to the end, avoiding positions too near to the bot
        position = state.cards_left - (state.alive_bots - 1)  # Place it just out of reach of the bot
        print(f"Placing Exploding Kitten in a position that maximizes risk for other players: {position}")
        return position

    def track_game_history(self, state: GameState):
        """
        Use the game's history to gain insights and adjust gameplay.
        """
        self._track_exploding_kittens(state)
        self._track_skip_cards(state)
        self._warn_about_defuses(state)

    def _track_exploding_kittens(self, state: GameState):
        """
        Track how many Exploding Kittens have been played.
        """
        exploding_kittens_played = [
            card for card in state.history_of_played_cards if card.card_type == CardType.EXPLODING_KITTEN
        ]
        print(f"Exploding Kittens removed from the game: {len(exploding_kittens_played)}")

    def _track_skip_cards(self, state: GameState):
        """
        Track SKIP cards played by opponents.
        """
        skips_played = [
            card for card in state.history_of_played_cards if card.card_type == CardType.SKIP
        ]
        print(f"SKIP cards played so far: {len(skips_played)}")

    def _warn_about_defuses(self, state: GameState):
        """
        Adjust strategy if most DEFUSE cards are gone.
        """
        defuses_played = [
            card for card in state.history_of_played_cards if card.card_type == CardType.DEFUSE
        ]
        if len(defuses_played) >= state.alive_bots:
            print("Most players are out of DEFUSE cards. Play cautiously!")

