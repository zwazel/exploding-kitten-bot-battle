"""
Test bot for development and testing.

This bot demonstrates the Bot interface and can be used as a reference
for students implementing their own bots.
"""

from game.bots.base import (
    Action,
    Bot,
    DrawCardAction,
    PassAction,
    PlayCardAction,
    PlayComboAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.history import GameEvent


class TestBot(Bot):
    """
    A simple test bot that plays basic cards when possible.
    
    Strategy:
    - Plays Skip or Attack cards when available
    - Otherwise draws a card to end the turn
    - Plays Nope cards as reactions 50% of the time
    """
    
    def __init__(self) -> None:
        """Initialize the test bot."""
        self._name: str = "TestBot"
    
    @property
    def name(self) -> str:
        return self._name
    
    def take_turn(self, view: BotView) -> Action:
        """
        Take a turn by playing a card or drawing.
        
        Priority:
        1. Play Skip card (avoids drawing)
        2. Play Attack card (makes opponent take extra turns)
        3. Draw a card (end turn normally)
        """
        # Look for playable action cards
        for card in view.my_hand:
            if card.card_type == "SkipCard" and card.can_play(view, is_own_turn=True):
                return PlayCardAction(card=card)
        
        for card in view.my_hand:
            if card.card_type == "AttackCard" and card.can_play(view, is_own_turn=True):
                return PlayCardAction(card=card)
        
        # Check if we can play a 2-of-a-kind combo
        combo_cards: list[Card] = self._find_two_of_a_kind(view)
        if combo_cards and view.other_players:
            return PlayComboAction(
                cards=tuple(combo_cards),
                target_player_id=view.other_players[0],
            )
        
        # Default: draw a card to end turn
        return DrawCardAction()
    
    def _find_two_of_a_kind(self, view: BotView) -> list[Card]:
        """Find two cards of the same type that can combo."""
        card_types: dict[str, list[Card]] = {}
        
        for card in view.my_hand:
            if card.can_combo():
                if card.card_type not in card_types:
                    card_types[card.card_type] = []
                card_types[card.card_type].append(card)
        
        for cards in card_types.values():
            if len(cards) >= 2:
                return cards[:2]
        
        return []
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        """
        React to game events.
        
        This test bot just logs events, but a smarter bot could
        track what cards other players have used.
        """
        # For now, we don't need to track anything
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        """
        Decide whether to play a reaction card.
        
        This bot plays Nope cards when it has them, targeting actions
        that would hurt it directly.
        """
        # Find a Nope card
        for card in view.my_hand:
            if card.card_type == "NopeCard" and card.can_play_as_reaction():
                # Only nope if the action targets us or is an attack
                event_data: dict = triggering_event.data
                if (
                    event_data.get("target") == view.my_id
                    or triggering_event.data.get("card_type") == "AttackCard"
                ):
                    return PlayCardAction(card=card)
        
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        """
        Choose where to reinsert the Exploding Kitten.
        
        This bot places it near the top (risky for next player).
        """
        # Place it 3 cards from the top if possible
        if draw_pile_size >= 3:
            return draw_pile_size - 3
        return 0  # Bottom if pile is small
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        """
        Choose a card to give when targeted by Favor.
        
        This bot gives the least valuable card (cat cards first, then others).
        """
        hand: tuple[Card, ...] = view.my_hand
        
        # Try to give a cat card (least useful alone)
        for card in hand:
            if card.card_type.endswith("CatCard"):
                return card
        
        # Otherwise give the first card that's not a Defuse or Nope
        for card in hand:
            if card.card_type not in ("DefuseCard", "NopeCard"):
                return card
        
        # Last resort: give the first card
        return hand[0]
