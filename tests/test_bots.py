from bot import Bot
from card import Card, CardType


class CheaterPlayBot(Bot):
    """Bot that attempts to play a card it created itself."""

    def __init__(self):
        super().__init__("cheater_play")
        self.cheated = False

    def play(self, state):
        if not self.cheated:
            self.cheated = True
            fake = Card(CardType.SKIP)
            self.add_card(fake)
            return fake
        return None

    def handle_exploding_kitten(self, state):
        return 0

    def see_the_future(self, state, top_three):
        pass


class CheaterDefuseBot(Bot):
    """Bot that tries to survive by fabricating a defuse card."""

    def __init__(self):
        super().__init__("cheater_defuse")

    def play(self, state):
        # remove any real defuse cards
        self.hand = [c for c in self.hand if c.card_type != CardType.DEFUSE]
        # add a fake defuse card
        fake = Card(CardType.DEFUSE)
        self.add_card(fake)
        return None

    def handle_exploding_kitten(self, state):
        return 0

    def see_the_future(self, state, top_three):
        pass


class SkipBot(Bot):
    """Bot that always plays the first valid skip card it finds."""

    def __init__(self):
        super().__init__("skipbot")

    def play(self, state):
        for card in self.hand:
            if card.card_type == CardType.SKIP:
                return card
        return None

    def handle_exploding_kitten(self, state):
        return 0

    def see_the_future(self, state, top_three):
        pass


class SeeFutureBot(Bot):
    """Bot that records the result of a See the Future card."""

    def __init__(self):
        super().__init__("seer")
        self.seen = None

    def play(self, state):
        for card in self.hand:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card
        return None

    def handle_exploding_kitten(self, state):
        return 0

    def see_the_future(self, state, top_three):
        self.seen = top_three
