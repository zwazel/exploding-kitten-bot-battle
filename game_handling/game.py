""" This module contains the Game class, which is responsible for handling the game logic. """
from random import shuffle
from typing import List, Optional

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
        self._game_state = GameState(
            total_cards_in_deck=card_counts,
            cards_left_to_draw=self.deck.cards_left(),
            history_of_played_cards=[],
            alive_bots=len(bots),
            turns_left=0
        )
        self._dead_bots = []

    def reset(self, card_counts: CardCounts, bots: List[Bot]) -> None:
        """
        Resets the game state
        :param card_counts: CardCounts object
        :param bots: List of Bot objects
        
        """
        self.deck = Deck(card_counts, len(bots))
        self.current_bot_index = 0
        self._game_state = GameState(
            total_cards_in_deck=card_counts,
            cards_left_to_draw=self.deck.cards_left(),
            history_of_played_cards=[],
            alive_bots=len(bots),
            turns_left=0
        )
        self.bots = bots
        self.dead_bots = []

    def setup(self) -> None:
        """
        Initializes the bots' hands
        :return: None
        """
        self.deck.initialize_bot_hands(self.bots, self.game_state.total_cards_in_deck)

    def play_game(self):
        """
        Plays one round of the game
        :return: List of Bot objects, [0]=loser ... [n]=winner
        """
        print('Game started!\n')
        shuffle(self.bots)  # Randomize the order of the bots

        while len(self.bots) > 1:
            # Determine the current bot
            current_bot = self.bots[self.current_bot_index]
            self.game_state.turns_left += 1
            # Let one bot make all his moves
            while current_bot in self.bots and self.game_state.turns_left > 0:
                action = self.play_turn(current_bot)
                self.game_state.turns_left -= 1
                if action == 'attack':
                    self.game_state.turns_left += 1
                    break

                # Draw a card, if needed
                if action == 'other':
                    self.draw_card(current_bot)
                    if current_bot in self.bots: # Check if the bot is still alive
                        self.inform_all_bots(current_bot, None)

            if current_bot in self.bots:
                self.show_hand(current_bot)  # Show the hand of the current bot
            if not self.testing:
                # await user input for next turn
                input('Press Enter to continue...')
            # Move to the next bot
            self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
        # The game is over
        return self.bots[0]

    def play_turn(self, current_bot: Bot) -> str:
        """
        Plays one turn for the current bot
        :param current_bot: Bot object
        :return: str  The result of the turn
        - attack: The bot played an attack card
        - skip: The bot played a skip card
        - other: The bot played another card
        """
        print(f'{current_bot.name}\'s turn')

        while True:
            card_type = self.play_card(current_bot)
            self.inform_all_bots(current_bot, card_type)
            if card_type == CardType.ATTACK:
                return 'attack'
            elif card_type == CardType.SKIP:
                return 'skip'
            else:
                return 'other'

    def play_card(self, current_bot: Bot) -> Optional[CardType]:
        """
        Asks the bot to play a card and handles the card played
        """
        card_played = current_bot.play(self.game_state)
        if card_played is None:
            print(f'{current_bot.name} did not play a card!')
            return None
        if card_played not in current_bot.hand:
            print(f'{current_bot.name} tried to play a card that is not in his hand!')
            return None
        if card_played.card_type == CardType.DEFUSE:
            print(f'{current_bot.name} played a defuse card! Is the bot stupid?')
            return None

        if card_played.card_type not in CardType:
            print(f'{current_bot.name} tried to play an invalid card!')
            return None

        print(f'{current_bot.name} played a {card_played.card_type} card!')
        self.handle_card_play(current_bot, card_played)
        return card_played.card_type

    def inform_all_bots(self, current_bot: Bot, card_type: CardType = None) -> None:
        """
        Informs all bots about the played card
        :param current_bot: Bot object
        :param card_type: Type of card played
        :return: None
        """
        current_bot_index = self.bots.index(current_bot)
        offset = 0
        for bot in self.bots:
            other_bot_index = self.bots.index(bot)
            offset = other_bot_index - current_bot_index
            if offset < 0:
                offset += len(self.bots)
            if not card_type:
                bot.card_drawn(offset)
            else:
                bot.card_played(card_type, offset)

    def draw_card(self, current_bot: Bot):
        """
        Draws a card for the bot
        :param current_bot: Bot object
        :return: None
        """
        drawn_card = self.deck.draw()
        print(f'{current_bot.name} drew {drawn_card.card_type.name}')
        if drawn_card.card_type == CardType.EXPLODING_KITTEN:
            print(f'Oh no, {current_bot.name} drew an exploding kitten!')
            if current_bot.has_defuse():
                print(f'{current_bot.name} used a defuse card')
                self.deck.discard(current_bot.use_defuse())
                insert_index = current_bot.handle_exploding_kitten(self.game_state)
                self.deck.insert_exploding_kitten(insert_index)
                print(
                    f'{current_bot.name} survived the exploding kitten and inserted the Exploding Kitten back into the deck at index {insert_index}')
                self.game_state.was_last_card_exploding_kitten = True
            else:
                current_bot.alive = False
                print(f'{current_bot.name} exploded!')
                self.game_state.was_last_card_exploding_kitten = False
                self.game_state.history_of_played_cards.append(drawn_card)
                self.game_state.alive_bots -= 1
                self.dead_bots.append(current_bot)
                self.bots.remove(current_bot)
        else:
            current_bot.add_card(drawn_card)

    def show_hand(self, current_bot: Bot) -> None:
        print(f'End of {current_bot.name}\'s turn')
        cards_left_string = ''
        for card in current_bot.hand:
            cards_left_string += card.card_type.name + ', '
        print(f'Cards left in {current_bot.name}\'s hand: {cards_left_string[:-2]}')
        print(f'Number of cards left in deck: {self.game_state.cards_left_to_draw}')
        print(f'Number of alive bots: {self.game_state.alive_bots}\n')

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
    def dead_bots(self):
        """ returns the dead_bots """
        return self._dead_bots

    @dead_bots.setter
    def dead_bots(self, value):
        """ sets the dead_bots """
        self._dead_bots = value
