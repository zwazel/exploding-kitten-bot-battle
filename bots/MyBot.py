from typing import List, Optional
from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class UltimateBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.future_cards: List[Card] = []  # Speichert die Karten aus "See the Future"
        self.cards_played: List[Card] = []  # Verfolgung der gespielten Karten
        self.total_exploding_kittens: int = 0  # Anzahl der Exploding Kittens im Spiel

    def play(self, state: GameState) -> Optional[Card]:
        """
        Entscheidet, welche Karte gespielt wird, basierend auf Wahrscheinlichkeiten und Strategie.
        """

        # Initialisiere die Anzahl der Exploding Kittens beim ersten Zug
        if self.total_exploding_kittens == 0:
            self.total_exploding_kittens = state.alive_bots - 1

        # Wahrscheinlichkeit des Ziehens eines Exploding Kittens
        exploding_kittens_left = self.total_exploding_kittens - len(
            [card for card in self.cards_played if card.card_type == CardType.EXPLODING_KITTEN]
        )
        probability_of_exploding = exploding_kittens_left / state.cards_left_to_draw

        # 1. Priorität: Vermeide Exploding Kittens
        if self.future_cards:
            if self.future_cards[0].card_type == CardType.EXPLODING_KITTEN:
                skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
                if skip_cards:
                    return skip_cards[0]

        # 2. Nutze "See the Future", um mehr Informationen zu sammeln
        see_the_future_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
        if see_the_future_cards:
            return see_the_future_cards[0]

        # 3. Spiele eine "SKIP"-Karte, wenn die Wahrscheinlichkeit hoch ist, ein Exploding Kitten zu ziehen
        if probability_of_exploding > 0.5:  # Risikogrenze angepasst, um mehr auf Sicherheit zu setzen
            skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
            if skip_cards:
                return skip_cards[0]

        # 4. Priorisiere "DEFUSE"-Karten: Bewahre sie auf, wenn sie noch nicht verwendet wurden
        defuse_cards = [card for card in self.hand if card.card_type == CardType.DEFUSE]
        if defuse_cards:
            # Bewahre "DEFUSE" für den Fall auf, dass ein Exploding Kitten gezogen wird
            return defuse_cards[0]

        # 5. Normale Karten spielen, um die Hand zu leeren und Risiken zu minimieren
        normal_cards = [card for card in self.hand if card.card_type == CardType.NORMAL]
        if normal_cards:
            return normal_cards[0]

        # 6. Wenn keine Karte gespielt wird, ziehe eine Karte
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Platzierung des Exploding Kittens: Lege die Karte strategisch an eine Position,
        die dem Gegner schadet, aber dir hilft.
        """
        # Wenn Exploding Kitten verfügbar, platziere sie an einer Position, wo der Gegner
        # sie vielleicht ziehen muss, aber du eine "DEFUSE"-Karte hast.
        return max(0, state.cards_left_to_draw - 2)

    def see_the_future(self, state: GameState, top_three: List[Card]):
        """
        Speichert die obersten drei Karten des Decks.
        """
        self.future_cards = top_three

    def update_played_cards(self, card: Card):
        """
        Verfolgt, welche Karten im Spiel verwendet wurden.
        """
        self.cards_played.append(card)