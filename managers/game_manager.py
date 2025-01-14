"""
Handles turns: Who’s playing, checking moves, shuffling decks.
Legal moves: Ensures bots return valid moves.
"""
from enum import Enum
from state import GameState
from typing import Dict
from bot_template import Bot

PlayersDict = Dict[str, Bot]


class MoveType(Enum):
    PLAY_CARD = "play_card"
    DRAW_CARD = "draw_card"


class GameManager:
    def __init__(self, players: PlayersDict):
        self.state = GameState(players)
        self.state.initialize_deck()

    def play_turn(self, bot: Bot):
        visible_state = self.state.get_visible_state(bot.name)
        move = bot.play(visible_state)

        # Validate the move
        if move["move"] == MoveType.PLAY_CARD and move["card"] in bot.hand:
            self.state.discard_pile.append(move["card"])
            bot.hand.remove(move["card"])
        elif move["move"] == MoveType.DRAW_CARD:
            if self.state.draw_pile:
                bot.hand.append(self.state.draw_pile.pop())
            else:
                print(f"{bot.name} tried to draw a card, but the deck is empty!")
        else:
            raise ValueError(f"Invalid move from {bot.name}: {move}")

    def check_end_game(self) -> bool:
        # Example end condition: only one bot left or all have exploded
        active_bots = [player for player in self.state.players.values() if player.name not in self.state.exploded_bots]
        return len(active_bots) <= 1
