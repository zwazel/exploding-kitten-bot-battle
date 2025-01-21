""" This module contains the Game class, which is responsible for handling the game logic. """
import sys
from typing import List

from bot import Bot
from card import Card, CardType, CardCounts
from deck import Deck
from game_handling.game_state import GameState


class Game:
    """
    The Game class is responsible for handling the game logic
    """

    def __init__(self, testing: bool, bots: List[Bot], card_counts: CardCounts):
        """
        Constructor for the Game class
        :param testing: bool whether the game is in testing mode
        :param bots: List of Bot objects
        :param card_counts: CardCounts object
        """
        self._testing = testing
        self._bots = bots
        self._deck = Deck(card_counts, len(bots))
        self._current_bot_index = 0
        self._game_state = GameState(card_counts, self.deck.cards_left(), False, [], len(bots))
        self._ranking = []

    def reset(self, card_counts: CardCounts, bots: List[Bot]) -> None:
        """
        Resets the game state
        :param card_counts: CardCounts object
        :param bots: List of Bot objects
        
        """
        self.deck = Deck(card_counts, len(bots))
        self.current_bot_index = 0
        self.game_state = GameState(card_counts, self.deck.cards_left(), False, [], len(bots))
        self.bots = bots
        self.ranking = []

    def setup(self) -> None:
        """
        Initializes the bots' hands
        :return: None
        """
        self.deck.initialize_bot_hands(self.bots, self.game_state.total_cards_in_deck)

    def play(self) -> Bot:
        """
        Starts the game
        :return: Bot object that won the game
        """
        print('Game started!')
        print()
        while sum(1 for bot in self.bots if bot.alive) > 1:
            current_bot = self.bots[self.current_bot_index]
            if current_bot.alive:
                print(f'{current_bot.name}\'s turn')
                while not self.take_turn(current_bot):
                    pass
            else:
                print(f'{current_bot.name} is dead, skipping turn')

            self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
            self.game_state.cards_left_to_draw = self.deck.cards_left()

            if current_bot.alive:
                print(f'End of {current_bot.name}\'s turn')
                cards_left_string = ''
                for card in current_bot.hand:
                    cards_left_string += card.card_type.name + ', '
                print(f'Cards left in {current_bot.name}\'s hand: {cards_left_string[:-2]}')
                print(f'Amount of cards left in deck: {self.game_state.cards_left_to_draw}')
                print(f'Amount of alive bots: {self.game_state.alive_bots}')
                print()

                if not self.testing:
                    # await user input for next turn
                    input('Press Enter to continue...')
            else:
                print()
        return next(bot for bot in self.bots if bot.alive)

    def take_turn(self, bot: Bot) -> bool:
        """
        Takes a turn for a bot
        :param bot: The bot taking the turn
        :return: True if the bot ended his turn, False if the bot did not end his turn (e.g. played a normal card)
        """
        card_played = bot.play(self.game_state)
        if card_played:
            # check if the card is in the bot's hand
            if card_played not in bot.hand:
                print(
                    f'{bot.name} tried to play a card they don\'t have, cheater detected? {card_played}. drawing a card',
                    file=sys.stderr)
            # check if the card is a defuse card (defuse cards can\'t be played)
            elif card_played.card_type == CardType.DEFUSE:
                print(f'{bot.name} tried to play a defuse card, is he dumb? drawing a card',
                      file=sys.stderr)
            else:
                print(f'{bot.name} played {card_played.card_type.name}')
                self.handle_card_play(bot, card_played)
                if card_played.card_type in [CardType.SKIP]:
                    print(f'{bot.name} played a skip card, they don\'t draw a card')
                    self.game_state.was_last_card_exploding_kitten = False
                    return True
                return False
        else:
            print(f'{bot.name} didn\'t play a card, drawing a card')

        drawn_card = self.deck.draw()
        print(f'{bot.name} drew {drawn_card.card_type.name}')
        if drawn_card.card_type == CardType.EXPLODING_KITTEN:
            print(f'Oh no, {bot.name} drew an exploding kitten!')
            if bot.has_defuse():
                print(f'{bot.name} used a defuse card')
                self.deck.discard(bot.use_defuse())
                insert_index = bot.handle_exploding_kitten(self.game_state)
                self.deck.insert_exploding_kitten(insert_index)
                print(
                    f'{bot.name} survived the exploding kitten and inserted the Exploding Kitten back into the deck at index {insert_index}')
                self.game_state.was_last_card_exploding_kitten = True
            else:
                bot.alive = False
                print(f'{bot.name} exploded!')
                self.game_state.was_last_card_exploding_kitten = False
                self.game_state.history_of_played_cards.append(drawn_card)
                self.game_state.alive_bots -= 1
                self.ranking.append(bot)
        else:
            bot.add_card(drawn_card)
        return True

    def handle_card_play(self, bot: Bot, card: Card) -> None:
        """
        Handles the card that the bot played
        :param bot: Bot object
        :param card: Card object
        :return: None
        """
        bot.remove_card(card)
        self.deck.discard(card)
        self.game_state.history_of_played_cards.append(card)

        if card.card_type == CardType.SEE_THE_FUTURE:
            print(f'{bot.name} can see the future!')
            top_three = self.deck.peek(3)

            top_three_string = ''
            for card in top_three:
                top_three_string += card.card_type.name + ', '
            print(f'Top three cards: {top_three_string[:-2]}')

            bot.see_the_future(self.game_state, top_three)

    @property
    def testing(self):
        """ returns the testing """
        return self._testing

    @testing.setter
    def testing(self, value):
        """ sets the testing """
        self._testing = value

    @property
    def bots(self):
        """ returns the bots """
        return self._bots

    @bots.setter
    def bots(self, value):
        """ sets the bots """
        self._bots = value

    @property
    def deck(self):
        """ returns the deck """
        return self._deck

    @deck.setter
    def deck(self, value):
        """ sets the deck """
        self._deck = value

    @property
    def current_bot_index(self):
        """ returns the current_bot_index """
        return self._current_bot_index

    @current_bot_index.setter
    def current_bot_index(self, value):
        """ sets the current_bot_index """
        self._current_bot_index = value

    @property
    def game_state(self):
        """ returns the game_state """
        return self._game_state

    @game_state.setter
    def game_state(self, value):
        """ sets the game_state """
        self._game_state = value

    @property
    def ranking(self):
        """ returns the ranking """
        return self._ranking

    @ranking.setter
    def ranking(self, value):
        """ sets the ranking """
        self._ranking = value
