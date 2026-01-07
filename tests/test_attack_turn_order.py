"""
Test that Attack card correctly gives the NEXT player (not the attacker) extra turns.

This test catches the bug where Attack would double-advance the turn order,
causing the wrong player to receive the extra turns.
"""

import pytest
from typing import Any

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
    
    def __init__(self, name: str, actions: list[Action] | None = None) -> None:
        self._name: str = name
        self._actions: list[Action] = actions or []
        self._action_index: int = 0
        self.turns_taken: int = 0
    
    @property
    def name(self) -> str:
        return self._name
    
    def set_actions(self, actions: list[Action]) -> None:
        self._actions = actions
        self._action_index = 0
    
    def take_turn(self, view: BotView) -> Action:
        self.turns_taken += 1
        
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


class TestAttackCardTurnOrder:
    """Tests that Attack card gives turns to the correct player."""
    
    def test_attack_gives_turns_to_next_player_not_attacker(self) -> None:
        """
        When Player A plays Attack, the NEXT player (Player B) should get 2 turns.
        Player A should NOT get another turn immediately after.
        
        Turn order: A -> B -> C
        After A plays Attack: B takes turn, B takes turn, then C
        """
        engine: GameEngine = GameEngine(seed=42)
        
        player_a = ScriptedBot("PlayerA")
        player_b = ScriptedBot("PlayerB")
        player_c = ScriptedBot("PlayerC")
        
        engine.add_bot(player_a)
        engine.add_bot(player_b)
        engine.add_bot(player_c)
        
        # Safe deck - no explosions
        engine.create_deck({
            "TacoCatCard": 40,
            "AttackCard": 5,
        })
        engine.setup_game(initial_hand_size=5)
        
        # Give PlayerA an Attack card
        attack_card = AttackCard()
        player_a_state = engine._state.get_player("PlayerA")
        if player_a_state:
            player_a_state.hand.append(attack_card)
        
        # Force turn order: A -> B -> C
        engine._turn_manager._turn_order = ["PlayerA", "PlayerB", "PlayerC"]
        engine._turn_manager._current_index = 0
        engine._turn_manager._turns_remaining = {"PlayerA": 1, "PlayerB": 1, "PlayerC": 1}
        engine._state._turn_order = ["PlayerA", "PlayerB", "PlayerC"]
        engine._state._current_player_index = 0
        
        # Reset turn counters
        player_a.turns_taken = 0
        player_b.turns_taken = 0
        player_c.turns_taken = 0
        
        # PlayerA plays Attack
        player_a.set_actions([PlayCardAction(card=attack_card)])
        engine._run_turn("PlayerA")
        
        # After Attack, the current player should be PlayerB (not PlayerA!)
        current = engine._turn_manager.current_player_id
        assert current == "PlayerB", \
            f"After Attack, current player should be PlayerB, got {current}"
        
        # PlayerB should have 2 turns
        turns_b = engine._turn_manager.get_turns_remaining("PlayerB")
        assert turns_b == 2, \
            f"PlayerB should have 2 turns after being attacked, got {turns_b}"
        
        # PlayerA should have 0 turns (their turn ended)
        turns_a = engine._turn_manager.get_turns_remaining("PlayerA")
        assert turns_a == 0, \
            f"PlayerA should have 0 turns after playing Attack, got {turns_a}"
    
    def test_attack_next_player_takes_two_separate_turns(self) -> None:
        """
        After Attack, the victim should take 2 separate turns.
        Each turn should result in one action (draw).
        """
        engine: GameEngine = GameEngine(seed=42)
        
        player_a = ScriptedBot("PlayerA")
        player_b = ScriptedBot("PlayerB")
        
        engine.add_bot(player_a)
        engine.add_bot(player_b)
        
        engine.create_deck({
            "TacoCatCard": 40,
            "AttackCard": 5,
        })
        engine.setup_game(initial_hand_size=5)
        
        attack_card = AttackCard()
        player_a_state = engine._state.get_player("PlayerA")
        if player_a_state:
            player_a_state.hand.append(attack_card)
        
        engine._turn_manager._turn_order = ["PlayerA", "PlayerB"]
        engine._turn_manager._current_index = 0
        engine._turn_manager._turns_remaining = {"PlayerA": 1, "PlayerB": 1}
        engine._state._turn_order = ["PlayerA", "PlayerB"]
        engine._state._current_player_index = 0
        
        player_a.turns_taken = 0
        player_b.turns_taken = 0
        
        # A plays Attack
        player_a.set_actions([PlayCardAction(card=attack_card)])
        engine._run_turn("PlayerA")
        
        # B should take 2 turns
        player_b.set_actions([DrawCardAction(), DrawCardAction()])
        
        # Run B's first turn
        engine._run_turn("PlayerB")
        assert engine._turn_manager.get_turns_remaining("PlayerB") == 1
        
        # Run B's second turn
        engine._run_turn("PlayerB")
        assert engine._turn_manager.get_turns_remaining("PlayerB") == 0
        
        # Now it should go back to A
        # The main loop would advance to A at this point
