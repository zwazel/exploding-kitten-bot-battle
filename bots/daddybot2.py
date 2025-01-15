# bots/UltimateKittenBot.py

from typing import List, Optional
from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState


class UltimateKittenBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        # Hier speichern wir weiterhin bools: True = Kitten, False = Keine Kitten
        self.future_info: List[bool] = []

        # Grobes "Gedächtnis" über Gegner: wie viele Defuses wir vermuten (Index = Bot-ID)
        # Da wir in diesem Rahmen nicht wissen, welche ID welcher Bot hat, machen wir z. B. ein dict:
        self.guess_defuses_of_others = {}

        # Kitten/Defuse-Tracking
        self.kittens_in_deck = 0
        self.defuses_used = 0
        self.exploded_kittens = 0

        # Turn-spezifische Variablen
        self.turn_actions_played = 0
        self.see_future_played_this_turn = 0

        # Wir merken uns die zuletzt bekannte Deckgröße, um zu erkennen, wenn andere Bots gezogen haben
        self.last_known_deck_size = None

    def play(self, state: GameState) -> Optional[Card]:
        # 1) Turn-Start-Update
        if self.turn_actions_played == 0:
            self._update_game_knowledge(state)
            self.see_future_played_this_turn = 0
            # Falls sich das Deck verändert hat, während wir nicht am Zug waren,
            # verschieben/entwerten wir unser future_info (s. _deck_change_shift).
            if self.last_known_deck_size is not None and state.cards_left_to_draw < self.last_known_deck_size:
                cards_drawn_by_others = self.last_known_deck_size - state.cards_left_to_draw
                self._deck_change_shift(cards_drawn_by_others)

            self.last_known_deck_size = state.cards_left_to_draw

        self.turn_actions_played += 1

        # 2) Falls top-Karte laut future_info eine Kitten ist => SKIP/None
        if self.future_info and self.future_info[0] is True:
            if not self.has_defuse():
                skip_card = self._get_card_from_hand(CardType.SKIP)
                if skip_card:
                    return skip_card
                return None
            else:
                # Wir haben Defuse => evtl. Skip, um Defuse zu sparen
                skip_card = self._get_card_from_hand(CardType.SKIP)
                if skip_card:
                    return skip_card
                return None

        # 3) Ansonsten: Standard-Strategie (SEE_THE_FUTURE, SKIP, NORMAL etc.)
        strategy = self._decide_strategy(state)
        card_to_play = self._decide_best_move(state, strategy)
        if card_to_play:
            self.hand.remove(card_to_play)
            return card_to_play

        # 4) Keine Aktion => Zug beenden => wir ziehen -> None
        #    future_info verschieben wir erst in _after_draw_update_future_info
        self._after_draw_update_future_info()
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        self._update_game_knowledge(state)

        total_defuses = state.total_cards_in_deck.DEFUSE
        defuses_left_in_game = total_defuses - self.defuses_used

        # Aggressiver: Versuche herauszufinden, ob "der nächste Bot" oder "viele Bots" wohl keine Defuse mehr haben.
        # Da wir hier keinen direkten Zugriff auf den Bot-Namen oder IDs haben, machen wir eine grobe Heuristik:
        # => Wenn nur noch 3-4 Bots leben und im Schnitt kaum Defuses im Spiel => oben rein
        if state.alive_bots <= 4 and defuses_left_in_game < state.alive_bots:
            print(f"[{self.name}] legt Kitten oben rein (vermute wenig Defuses bei anderen)!")
            return 0

        # Sonst: Standard = unten
        return state.cards_left_to_draw

    def see_the_future(self, state: GameState, top_three: List[Card]):
        # future_info neu setzen
        self.future_info.clear()
        for card in top_three:
            self.future_info.append(card.card_type == CardType.EXPLODING_KITTEN)
        print(f"[{self.name}] sees the future: {self.future_info}")

    # -----------------------------------
    # Erweiterte Logik
    # -----------------------------------
    def _deck_change_shift(self, number_of_cards_drawn: int):
        """
        Versucht grob abzubilden, dass andere Bots in unserer Abwesenheit 'number_of_cards_drawn' Karten gezogen haben.
        => future_info[0] ist weg, future_info[1] rückt hoch etc.
        => Falls 'number_of_cards_drawn' >= len(future_info), leeren wir future_info komplett.
        """
        for _ in range(number_of_cards_drawn):
            if self.future_info:
                self.future_info.pop(0)
            else:
                break

    def _after_draw_update_future_info(self):
        """Wenn wir selbst ziehen (play => None), verschieben wir future_info um 1."""
        if self.future_info:
            self.future_info.pop(0)

    # -----------------------------------
    # Decision Helpers
    # -----------------------------------
    def _decide_strategy(self, state: GameState) -> str:
        prob = self._kitten_probability(state)
        if prob > 0.5 and not self.has_defuse():
            return "defensive"
        if prob < 0.2 and self.has_defuse():
            return "offensive"
        return "neutral"

    def _decide_best_move(self, state: GameState, strategy: str) -> Optional[Card]:
        prob = self._kitten_probability(state)

        if strategy == "defensive":
            # Bis zu 3x see_the_future
            see_future_count = sum(1 for c in self.hand if c.card_type == CardType.SEE_THE_FUTURE)
            if see_future_count > 0 and self.see_future_played_this_turn < 3:
                if prob > 0.4:
                    card = self._get_card_from_hand(CardType.SEE_THE_FUTURE)
                    if card:
                        self.see_future_played_this_turn += 1
                        return card
            # Dann SKIP falls prob > 0.5
            if prob > 0.5 and not self.has_defuse():
                skip_card = self._get_card_from_hand(CardType.SKIP)
                if skip_card:
                    return skip_card
            return None

        elif strategy == "offensive":
            # Wirf Normal ab (mindgames)
            normal_card = self._get_card_from_hand(CardType.NORMAL)
            if normal_card:
                return normal_card
            # 1x see_the_future wenn prob > 0.1
            if self.see_future_played_this_turn < 1 and prob > 0.1:
                sf_card = self._get_card_from_hand(CardType.SEE_THE_FUTURE)
                if sf_card:
                    self.see_future_played_this_turn += 1
                    return sf_card
            return None

        else:  # neutral
            if 0.2 <= prob <= 0.45 and self.see_future_played_this_turn < 2:
                sf_card = self._get_card_from_hand(CardType.SEE_THE_FUTURE)
                if sf_card:
                    self.see_future_played_this_turn += 1
                    return sf_card
            return None

    # -----------------------------------
    # Knowledge / State Tracking
    # -----------------------------------
    def _update_game_knowledge(self, state: GameState):
        self.turn_actions_played = 0

        total_ek = state.total_cards_in_deck.EXPLODING_KITTEN
        exploded = sum(1 for c in state.history_of_played_cards if c.card_type == CardType.EXPLODING_KITTEN)
        self.exploded_kittens = exploded
        self.kittens_in_deck = max(0, total_ek - exploded)

        total_def = state.total_cards_in_deck.DEFUSE
        used_def = sum(1 for c in state.history_of_played_cards if c.card_type == CardType.DEFUSE)
        self.defuses_used = used_def

    def _kitten_probability(self, state: GameState) -> float:
        if state.cards_left_to_draw <= 0:
            return 0.0
        return self.kittens_in_deck / state.cards_left_to_draw

    def _get_card_from_hand(self, ctype: CardType) -> Optional[Card]:
        for card in self.hand:
            if card.card_type == ctype:
                return card
        return None
