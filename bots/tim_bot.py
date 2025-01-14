from bot_template import Bot, MoveType, Move

class TimBot(Bot):
    def __init__(self):
        super().__init__("Tim Bot")

    def play(self, game_state: dict) -> Move:
        """
        Make a decision for the current turn.
        "game_state" provides information about the bot's hand, remaining draw cards,
        last played cards, and the counts of each card type.
        """
        hand = game_state["hand"]

        # Example strategy: play "Skip" if available, otherwise draw a card.
        for card in hand:
            if card == "Skip":
                return {"move": MoveType.PLAY_CARD, "card": "Skip"}

        # No "Skip" available, draw a card.
        return {"move": MoveType.DRAW_CARD, "card": None}