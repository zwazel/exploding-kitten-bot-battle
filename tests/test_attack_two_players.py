"""
Test Attack card with only 2 players - catches the double-advance bug.
"""

import pytest

from game.engine import GameEngine
from game.bots.base import (
    Bot,
    Action,
    DrawCardAction,
    PlayCardAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.cards.action_cards import AttackCard
from game.history import EventType, GameEvent


class ScriptedBot(Bot):
    """A bot that follows a script of actions."""
    
    def __init__(self, name: str) -> None:
        self._name: str = name
        self._actions: list[Action] = []
        self._action_index: int = 0
    
    @property
    def name(self) -> str:
        return self._name
    
    def set_actions(self, actions: list[Action]) -> None:
        self._actions = actions
        self._action_index = 0
    
    def take_turn(self, view: BotView) -> Action:
        if self._action_index < len(self._actions):
            action = self._actions[self._action_index]
            self._action_index += 1
            return action
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        return view.my_hand[0]
    
    def on_explode(self, view: BotView) -> None:
        pass


class TestAttackWithTwoPlayers:
    """Tests Attack card with only 2 players to catch double-advance bug."""
    
    def test_attack_with_two_players_gives_opponent_turns(self) -> None:
        """
        With 2 players (A and B), when A plays Attack:
        - B should get 2 turns
        - A should NOT immediately get another turn
        
        Turn order: A -> B -> A -> B...
        After A plays Attack: B should be current with 2 turns
        """
        engine: GameEngine = GameEngine(seed=42)
        
        player_a = ScriptedBot("PlayerA")
        player_b = ScriptedBot("PlayerB")
        
        engine.add_bot(player_a)
        engine.add_bot(player_b)
        
        engine.create_deck({"TacoCatCard": 40})
        engine.setup_game(initial_hand_size=5)
        
        attack_card = AttackCard()
        player_a_state = engine._state.get_player("PlayerA")
        if player_a_state:
            player_a_state.hand.append(attack_card)
        
        # Force turn order: A -> B
        engine._turn_manager._turn_order = ["PlayerA", "PlayerB"]
        engine._turn_manager._current_index = 0
        engine._turn_manager._turns_remaining = {"PlayerA": 1, "PlayerB": 1}
        engine._state._turn_order = ["PlayerA", "PlayerB"]
        engine._state._current_player_index = 0
        
        # A plays Attack
        player_a.set_actions([PlayCardAction(card=attack_card)])
        engine._run_turn("PlayerA")
        
        # After Attack, current should be B (NOT A!)
        current = engine._turn_manager.current_player_id
        assert current == "PlayerB", \
            f"After Attack with 2 players, current should be PlayerB, got {current}"
        
        # B should have 2 turns
        turns_b = engine._turn_manager.get_turns_remaining("PlayerB")
        assert turns_b == 2, \
            f"PlayerB should have 2 turns, got {turns_b}"
        
        # Now simulate what the main loop does: check if previous player has 0 turns
        # This is where the bug occurs - it would advance AGAIN
        alive = engine._state.get_alive_players()
        if engine._turn_manager.get_turns_remaining("PlayerA") == 0:
            # The main loop would call advance_to_next_player here
            # But the Attack card ALREADY advanced! This is the bug.
            pass
        
        # The current player should STILL be PlayerB
        current_after = engine._turn_manager.current_player_id
        assert current_after == "PlayerB", \
            f"Current player should still be PlayerB, got {current_after}"
