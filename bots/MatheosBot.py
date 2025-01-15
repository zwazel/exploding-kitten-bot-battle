import random
from typing import List, Optional

from bot import Bot
from card import Card, CardType
from game_handling.game_state import GameState

class Matheos(Bot):
    risk=False
    See=False
    topC=[]
    cards=0
    used=False
    def play(self, state: GameState) -> Optional[Card]:
        See_cards = [card for card in self.hand if card.card_type == CardType.SEE_THE_FUTURE]
        Skip_cards = [card for card in self.hand if card.card_type == CardType.SKIP]
        def_cards=[card for card in self.hand if card.card_type == CardType.DEFUSE]
        curTop=(self.cards)-(state.cards_left)
        if curTop==1 and Skip_cards and self.topC[1].card_type==CardType.EXPLODING_KITTEN:
            return random.choice(Skip_cards)
        if curTop==2 and Skip_cards and self.topC[2].card_type==CardType.EXPLODING_KITTEN:
            return random.choice(Skip_cards)
        riskfactor=(state.alive_bots-1)/(state.cards_left)
        if riskfactor<0.2:
            print("low risk")
            return None
        if See_cards and self.See==False and Skip_cards:
            self.See=True
            return random.choice(See_cards)
        if Skip_cards and self.risk==True:
            return random.choice(Skip_cards)
        if len(Skip_cards)>3 and self.used!=True and riskfactor> 0.3:
            return random.choice(Skip_cards)
        if len(Skip_cards)>2 and self.used!=True and riskfactor> 0.4:
            return random.choice(Skip_cards)
        if Skip_cards and self.used!=True and riskfactor> 0.5:
            return random.choice(Skip_cards)
        self.used=False
        self.See=False
        self.risk=False
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        return 0

    def see_the_future(self, state: GameState, top_three: List[Card]):
        self.topC=top_three
        self.cards = state.cards_left
        self.used=True
        if top_three[0] == CardType.EXPLODING_KITTEN:
            self.risk=True
        pass
