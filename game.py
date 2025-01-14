from typing import List, Optional
from card import Card, CardType, CardCounts
from deck import Deck
from bot import Bot
from game_state import GameState

class Game:
    def __init__(self, bots: List[Bot], card_counts: CardCounts):
        self.bots = bots
        self.deck = Deck(card_counts)
        self.current_bot_index = 0
        self.game_state = GameState(bots, self.current_bot_index, card_counts, self.deck.cards_left())

    def setup(self):
        self.deck.initialize(len(self.bots))
        for bot in self.bots:
            bot.add_card(Card(CardType.DEFUSE))
            for _ in range(4):
                bot.add_card(self.deck.draw())

    def play(self) -> Bot:
        while len(self.bots) > 1:
            current_bot = self.bots[self.current_bot_index]
            self.take_turn(current_bot)
            self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
            self.game_state.current_bot_index = self.current_bot_index
            self.game_state.cards_left = self.deck.cards_left()
        return self.bots[0]

    def take_turn(self, bot: Bot):
        turns_to_play = 1
        while turns_to_play > 0:
            card_played = bot.play(self.deck.cards_left())
            if card_played:
                self.handle_card_play(bot, card_played)
                if card_played.card_type in [CardType.SKIP, CardType.ATTACK]:
                    break
            else:
                drawn_card = self.deck.draw()
                if drawn_card.card_type == CardType.EXPLODING_KITTEN:
                    if bot.has_defuse():
                        self.deck.discard(bot.use_defuse())
                        insert_index = bot.handle_exploding_kitten()
                        self.deck.insert_exploding_kitten(insert_index)
                    else:
                        self.bots.remove(bot)
                        if len(self.bots) == 1:
                            return
                else:
                    bot.add_card(drawn_card)
                turns_to_play -= 1

    def handle_card_play(self, bot: Bot, card: Card):
        bot.remove_card(card)
        self.deck.discard(card)
        for player in self.bots:
            player.add_last_played(card)

        if card.card_type == CardType.ATTACK:
            self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
            self.take_turn(self.bots[self.current_bot_index])
            self.current_bot_index = (self.current_bot_index - 1) % len(self.bots)
        elif card.card_type == CardType.SEE_THE_FUTURE:
            top_three = self.deck.peek(3)
            bot.see_the_future(top_three)