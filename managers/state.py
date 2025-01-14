"""
Keeps track of the draw pile, discard pile, player hands, etc.
"""
import random

from game_manager import PlayersDict


class GameState:
    def __init__(self, players: PlayersDict):
        self.players = players  # Dictionary of player names to Player objects
        self.draw_pile = []
        self.discard_pile = []
        self.exploded_bots = []
        self.last_played_cards = []

    def initialize_deck(self):
        num_players = len(self.players)
        self.draw_pile = (
                ["Exploding Kitten"] * (num_players - 1) +
                ["Defuse"] * num_players +
                ["Skip"] * (num_players * 2) +
                ["Attack"] * (num_players * 2) +
                ["See the Future"] * num_players +
                ["Normal"] * (num_players * 3)
        )
        random.shuffle(self.draw_pile)

    def get_visible_state(self, player_name):
        return {
            "hand": self.players[player_name].hand,
            "remaining_draw_cards": len(self.draw_pile),
            "discard_pile": self.discard_pile[-5:],
            "card_counts": {card_type: self.draw_pile.count(card_type) + self.discard_pile.count(card_type) for
                            card_type in ["Exploding Kitten", "Defuse", "Skip", "Attack", "See the Future", "Normal"]},
        }
