""" This file contains the GameState class, which is used to store the current state of the game. """
from dataclasses import dataclass

from card import CardCounts, Card


@dataclass
class GameState:
    """
    This class is used to store the current state of the game.
    """
    # the number of cards in the deck at the start of the game
    total_cards_in_deck: CardCounts
    # the number of cards left in the draw deck
    cards_left_to_draw: int

    '''
    the history of the cards played
    exploding kitten cards are also added to this list, if they were NOT returned to the deck (they're out of the game now, so, in a way, "played")
    '''
    history_of_played_cards: list[Card]
    # how many bots are still alive
    alive_bots: int
    # how many turns the current bot has to play
    turns_left: int
