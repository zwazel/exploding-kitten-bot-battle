import sys
import json
from typing import List

from bot import Bot
from card import Card, CardType, CardCounts
from deck import Deck
from game_handling.game_state import GameState


class Game:
    def __init__(self, testing: bool, bots: List[Bot], card_counts: CardCounts):
        self.testing = testing
        self.bots = bots
        self.deck = Deck(card_counts, len(bots))
        self.current_bot_index = 0
        self.game_state = GameState(card_counts, self.deck.cards_left(), False, [], len(bots))
        self.events: list[dict] = []

    def reset(self, card_counts: CardCounts, bots: List[Bot]):
        self.deck = Deck(card_counts, len(bots))
        self.current_bot_index = 0
        self.game_state = GameState(card_counts, self.deck.cards_left(), False, [], len(bots))
        self.bots = bots
        self.events = []

    def setup(self):
        self.deck.initialize_bot_hands(self.bots, self.game_state.total_cards_in_deck)
        for bot in self.bots:
            self.log_event(
                "initial_hand",
                bot=bot.name,
                cards=[{"type": c.card_type.value, "id": c.id} for c in bot.hand],
            )

    def log_event(self, event_type: str, **data):
        self.events.append({"event": event_type, **data})

    def export_log(self, path: str):
        with open(path, "w") as f:
            json.dump(self.events, f, indent=2)

    def play(self) -> Bot:
        print("Game started!")
        print()
        self.log_event("game_start")
        while sum(1 for bot in self.bots if bot.alive) > 1:
            current_bot = self.bots[self.current_bot_index]
            if current_bot.alive:
                print(f"{current_bot.name}'s turn")
                self.log_event("turn_start", bot=current_bot.name)
                while not self.take_turn(current_bot):
                    pass
            else:
                print(f"{current_bot.name} is dead, skipping turn")
                self.log_event("turn_start", bot=current_bot.name, skipped=True)

            self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
            self.game_state.cards_left_to_draw = self.deck.cards_left()

            cards_left_string = ""
            for card in current_bot.hand:
                cards_left_string += card.card_type.name + ", "
            if current_bot.alive:
                print(f"End of {current_bot.name}'s turn")
                print(f"Cards left in {current_bot.name}'s hand: {cards_left_string[:-2]}")
                print(f"Amount of cards left in deck: {self.game_state.cards_left_to_draw}")
                print(f"Amount of alive bots: {self.game_state.alive_bots}")
                print()

                if not self.testing:
                    # await user input for next turn
                    input("Press Enter to continue...")
            else:
                print()

            self.log_event(
                "turn_end",
                bot=current_bot.name,
                hand=[{"type": c.card_type.value, "id": c.id} for c in current_bot.hand],
                deck_count=self.game_state.cards_left_to_draw,
                alive_bots=self.game_state.alive_bots,
                alive=current_bot.alive,
            )
        winner = next(bot for bot in self.bots if bot.alive)
        self.log_event("game_end", winner=winner.name)
        return winner

    def take_turn(self, bot: Bot) -> bool:
        """

        :param bot: The bot taking the turn
        :return: True if the bot ended his turn, False if the bot did not end his turn (e.g. played a normal card)
        """
        card_played = bot.play(self.game_state)
        if card_played:
            # check if the card is legitimate and in the bot's hand
            if not self.deck.is_valid_card(card_played):
                print(
                    f"{bot.name} tried to play an invalid card, cheater detected? {card_played}. drawing a card",
                    file=sys.stderr,
                )
            elif card_played not in bot.hand:
                print(
                    f"{bot.name} tried to play a card they don't have, cheater detected? {card_played}. drawing a card",
                    file=sys.stderr,
                )
            # check if the card is a defuse card (defuse cards can't be played)
            elif card_played.card_type == CardType.DEFUSE:
                print(f"{bot.name} tried to play a defuse card, is he dumb? drawing a card", file=sys.stderr)
            else:
                print(f"{bot.name} played {card_played.card_type.name}")
                self.handle_card_play(bot, card_played)
                self.log_event(
                    "card_played",
                    bot=bot.name,
                    card_type=card_played.card_type.value,
                    card_id=card_played.id,
                )
                if card_played.card_type in [CardType.SKIP]:
                    print(f"{bot.name} played a skip card, they don't draw a card")
                    self.game_state.was_last_card_exploding_kitten = False
                    return True
                return False
        else:
            print(f"{bot.name} didn't play a card, drawing a card")

        drawn_card = self.deck.draw()
        print(f"{bot.name} drew {drawn_card.card_type.name}")
        self.log_event(
            "card_drawn",
            bot=bot.name,
            card_type=drawn_card.card_type.value,
            card_id=drawn_card.id,
        )
        if drawn_card.card_type == CardType.EXPLODING_KITTEN:
            print(f"Oh no, {bot.name} drew an exploding kitten!")
            valid_defuses = [c for c in bot.hand if c.card_type == CardType.DEFUSE and self.deck.is_valid_card(c)]
            if valid_defuses:
                defuse_card = valid_defuses[0]
                bot.remove_card(defuse_card)
                print(f"{bot.name} used a defuse card")
                self.deck.discard(defuse_card)
                self.log_event("defuse_used", bot=bot.name, card_id=defuse_card.id)
                insert_index = bot.handle_exploding_kitten(self.game_state)
                self.deck.insert_exploding_kitten(insert_index, drawn_card)
                self.log_event(
                    "exploding_kitten_returned",
                    bot=bot.name,
                    index=insert_index,
                    card_id=drawn_card.id,
                )
                print(
                    f"{bot.name} survived the exploding kitten and inserted the Exploding Kitten back into the deck at index {insert_index}"
                )
                self.game_state.was_last_card_exploding_kitten = True
            else:
                bot.alive = False
                print(f"{bot.name} exploded!")
                self.deck.discard(drawn_card)
                self.game_state.was_last_card_exploding_kitten = False
                self.game_state.history_of_played_cards.append(drawn_card)
                self.game_state.alive_bots -= 1
                self.log_event("bot_exploded", bot=bot.name)
        else:
            bot.add_card(drawn_card)
        return True

    def handle_card_play(self, bot: Bot, card: Card):
        bot.remove_card(card)
        self.deck.discard(card)
        self.game_state.history_of_played_cards.append(card)

        if card.card_type == CardType.SEE_THE_FUTURE:
            print(f"{bot.name} can see the future!")
            top_three = self.deck.peek(3)

            top_three_string = ""
            for card in top_three:
                top_three_string += card.card_type.name + ", "
            print(f"Top three cards: {top_three_string[:-2]}")

            bot.see_the_future(self.game_state, top_three)
