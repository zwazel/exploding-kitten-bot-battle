from game import Bot, GameState, Card, CardType

class TalkativeBot(Bot):
    def play(self, state: GameState):
        self.say(f"I have {len(self.hand)} cards!")
        if self.has_card_type(CardType.ATTACK):
            self.say("Take that! ATTACK!")
            return self.hand[0] # logic is loose here
        if self.has_card_type(CardType.SKIP):
            self.say("Skipping my turn!")
            return next(c for c in self.hand if c.card_type == CardType.SKIP)
        if self.has_card_type(CardType.SHUFFLE):
            self.say("Everyday I'm shufflin'!")
            return next(c for c in self.hand if c.card_type == CardType.SHUFFLE)
        if self.has_card_type(CardType.FAVOR):
            self.say("Do me a favor?")
            return next(c for c in self.hand if c.card_type == CardType.FAVOR)
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        self.say("Oh no! A kitten!")
        return 0

    def see_the_future(self, state: GameState, top_three):
        self.say(f"I see {len(top_three)} cards in the future.")

    def choose_target(self, state, alive_players, context):
        self.say("Choosing a target...")
        return alive_players[0]

    def choose_card_from_hand(self, state):
        self.say("Here, take this.")
        return self.hand[0]

    def choose_card_type(self, state):
        self.say("I want a Defuse!")
        return CardType.DEFUSE

    def choose_from_discard(self, state, discard_pile):
        self.say("I'll take that back.")
        return discard_pile[-1]

    def on_action_played(self, state, action, actor):
        pass

    def should_play_nope(self, state, action):
        return False
