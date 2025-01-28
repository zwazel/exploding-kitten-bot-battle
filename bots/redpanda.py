from typing import List, Optional
from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState

class StrategicBot(Bot):
    def __init__(self, name):
        super().__init__(name)
        self.player_defuse_status = {}
        self.current_player = 0
        self.future_cards = []

    def play(self, state: GameState) -> Optional[Card]:
        """
        Wähle eine Karte, die sinnvoll ist, basierend auf den aktuellen Informationen.
        """
        # See the Future
        for card in self.hand:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card

        # Skip
        if state.cards_left_to_draw > 0 and any(
            card.card_type == CardType.EXPLODING_KITTEN for card in self.future_cards
        ):
            for card in self.hand:
                if card.card_type == CardType.SKIP:
                    return card

        # normale Karte
        for card in self.hand:
            if card.card_type == CardType.NORMAL:
                return card


        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        handle exploding kitten
        """
        next_player = self.calculate_next_player(state)
        if not self.player_defuse_status.get(next_player, False):
            # KEINE Defuse-Karte -> oberste Karte vom Stapel
            return 0
        else:
            # Defuse-Karte -> 5 position vom Stapel
            return min(4, state.cards_left_to_draw - 1)

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        See the Future + speicher nächsten Karten
        """
        self.future_cards = top_three
        if any(card.card_type == CardType.EXPLODING_KITTEN for card in top_three):
            print("Warnung: Exploding Kitten in den nächsten drei Karten")

    def update_player_defuse_status(self, player_id: int, has_defuse: bool):
        """
        Aktualisiere Defuse-Status eines Spielers.
        """
        self.player_defuse_status[player_id] = has_defuse

    def calculate_next_player(self, state: GameState) -> int:
        """
        Berechne den nächsten Spieler basierend auf der Anzahl der lebenden Bots.
        """
        return (self.current_player + 1) % state.alive_bots

    def analyze_game_state(self, state: GameState):
        """
        Analysiere den Spielstatus und aktualisiere Informationen über andere Spieler.
        """
        for player_id in range(state.alive_bots):
            if player_id != self.current_player:
                self.update_player_defuse_status(player_id, True)

    def update_current_player(self, state: GameState):
        """
        Aktualisiert den Index des aktuellen Spielers am Ende des Zuges.
        """
        self.current_player = self.calculate_next_player(state)

    def optimize_resource_usage(self, state: GameState):
        """
        Verbessert die Ressourcennutzung, indem Karten strategisch eingesetzt werden.
        """
        if self.future_cards and any(card.card_type == CardType.EXPLODING_KITTEN for card in self.future_cards):
            print("Exploding Kitten erkannt, Skip wird priorisiert.")

        if any(card.card_type == CardType.SKIP for card in self.hand):
            print("Skip-Karte verfügbar, Defuse wird geschont.")

    def adjust_to_endgame(self, state: GameState):
        """
        Passt die Strategie an das Endspiel an, um Exploding Kittens zu vermeiden.
        """
        if state.cards_left_to_draw <= 3:
            print("Endspiel-Strategie aktiviert: Exploding Kitten wird priorisiert umgangen.")
            for card in self.hand:
                if card.card_type == CardType.SKIP:
                    return card