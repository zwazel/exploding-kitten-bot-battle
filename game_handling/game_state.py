""" This file contains the GameState class, which is used to store the current state of the game. """
from dataclasses import dataclass

from card import CardCounts, Card


@dataclass
class GameState:
    """
    This class is used to store the current state of the game.
    """
    # the amount of cards in the deck at the start of the game
    total_cards_in_deck: CardCounts
    # the amount of cards left in the draw deck
    cards_left_to_draw: int
    '''
    This is TRUE if the last card drawn was an exploding kitten and was RETURNED to the deck by the last player (he had a defuse card and didn't explode).
    This is FALSE if the last card drawn was an exploding kitten and was NOT RETURNED to the deck by the last player (he didn't have a defuse card and exploded).
    This is also FALSE if the last card drawn was NOT an exploding kitten.
    '''
    was_last_card_exploding_kitten: bool
    '''
    the history of the cards played
    exploding kitten cards are also added to this list, if they were NOT returned to the deck (they're out of the game now, so, in a way, "played")
    '''
    history_of_played_cards: list[Card]
    # how many bots are still alive
    alive_bots: int
