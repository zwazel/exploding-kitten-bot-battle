from bot_class import Bot, MoveType

class ExampleBot(Bot):
    def __init__(self):
        super().__init__("Tim Bot")

    def play(self, game_state: dict) -> dict:
        # Example strategy: If we have a "Skip", play it, otherwise draw
        for card in game_state["hand"]:
            if card == "Skip":
                return {"move": MoveType.PLAY_CARD, "card": "Skip"}
        return {"move": MoveType.DRAW_CARD, "card": None}
