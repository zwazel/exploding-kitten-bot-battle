"""
Integration tests for Attack card multi-turn mechanics.

These tests verify that when a player is attacked:
1. They must take 2 turns (or more if attacks stack)
2. Each turn can be ended by drawing OR playing a Skip card
3. Cards drawn on turn 1 can be played on turn 2
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
from game.cards.action_cards import AttackCard, SkipCard
from game.history import EventType, GameEvent


class ScriptedBot(Bot):
    """
    A bot that follows a script of actions.
    
    Useful for testing specific game flows where we need
    precise control over what each bot does.
    """
    
    def __init__(self, name: str, actions: list[Action] | None = None) -> None:
        self._name: str = name
        self._actions: list[Action] = actions or []
        self._action_index: int = 0
        self.turns_taken: int = 0
        self.cards_drawn: list[Card] = []
    
    @property
    def name(self) -> str:
        return self._name
    
    def set_actions(self, actions: list[Action]) -> None:
        """Set the action script."""
        self._actions = actions
        self._action_index = 0
    
    def take_turn(self, view: BotView) -> Action:
        self.turns_taken += 1
        
        if self._action_index < len(self._actions):
            action = self._actions[self._action_index]
            self._action_index += 1
            return action
        
        # Default: draw a card
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        # Track cards drawn by this bot
        if event.event_type == EventType.CARD_DRAWN and event.player_id == self._name:
            pass  # Could track more details here
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        return view.my_hand[0]


class TestAttackCardMultipleTurns:
    """
    Tests that verify attacked players must take multiple turns.
    """
    
    def test_attack_gives_two_turns_draw_both(self) -> None:
        """
        When attacked, player can draw twice (one per turn).
        
        Flow:
        1. Attacker plays Attack card
        2. Victim draws card (ends turn 1)
        3. Victim draws card (ends turn 2)
        """
        engine: GameEngine = GameEngine(seed=42)
        
        attacker = ScriptedBot("Attacker")
        victim = ScriptedBot("Victim")
        
        engine.add_bot(attacker)
        engine.add_bot(victim)
        
        # Create deck with Attack cards and safe cards (no explosions)
        engine.create_deck({
            "AttackCard": 5,
            "SkipCard": 20,
            "TacoCatCard": 20,
        })
        engine.setup_game(initial_hand_size=5)
        
        # Find an Attack card in attacker's hand
        attacker_state = engine._state.get_player("Attacker")
        attack_card: Card | None = None
        if attacker_state:
            for card in attacker_state.hand:
                if card.card_type == "AttackCard":
                    attack_card = card
                    break
        
        # If attacker doesn't have Attack, give them one
        if attack_card is None:
            attack_card = AttackCard()
            if attacker_state:
                attacker_state.hand.append(attack_card)
        
        # Set up attacker to play Attack, victim to draw twice
        attacker.set_actions([PlayCardAction(card=attack_card)])
        victim.set_actions([DrawCardAction(), DrawCardAction()])
        
        # Force turn order: Attacker first
        engine._turn_manager._turn_order = ["Attacker", "Victim"]
        engine._turn_manager._current_index = 0
        engine._turn_manager._turns_remaining = {"Attacker": 1, "Victim": 1}
        engine._state._turn_order = ["Attacker", "Victim"]
        engine._state._current_player_index = 0
        
        # Run attacker's turn (plays Attack)
        engine._run_turn("Attacker")
        
        # Verify victim now has 2 turns
        assert engine._turn_manager.get_turns_remaining("Victim") == 2, \
            "Victim should have 2 turns after being attacked"
        
        # Run victim's first turn (draws)
        engine._run_turn("Victim")
        
        # Verify victim still has 1 turn remaining
        assert engine._turn_manager.get_turns_remaining("Victim") == 1, \
            "Victim should have 1 turn remaining after first draw"
        
        # Run victim's second turn (draws again)
        engine._run_turn("Victim")
        
        # Verify victim has no turns remaining
        assert engine._turn_manager.get_turns_remaining("Victim") == 0, \
            "Victim should have 0 turns remaining after second draw"
    
    def test_attack_gives_two_turns_skip_both(self) -> None:
        """
        When attacked, player can play 2 Skip cards (one per turn).
        
        Flow:
        1. Attacker plays Attack card
        2. Victim plays Skip (ends turn 1)
        3. Victim plays Skip (ends turn 2)
        """
        engine: GameEngine = GameEngine(seed=42)
        
        attacker = ScriptedBot("Attacker")
        victim = ScriptedBot("Victim")
        
        engine.add_bot(attacker)
        engine.add_bot(victim)
        
        engine.create_deck({
            "AttackCard": 5,
            "SkipCard": 20,
            "TacoCatCard": 20,
        })
        engine.setup_game(initial_hand_size=5)
        
        # Ensure attacker has Attack card
        attacker_state = engine._state.get_player("Attacker")
        attack_card: Card | None = None
        if attacker_state:
            for card in attacker_state.hand:
                if card.card_type == "AttackCard":
                    attack_card = card
                    break
        
        if attack_card is None:
            attack_card = AttackCard()
            if attacker_state:
                attacker_state.hand.append(attack_card)
        
        # Ensure victim has 2 Skip cards
        victim_state = engine._state.get_player("Victim")
        skip_cards: list[Card] = []
        if victim_state:
            for card in victim_state.hand:
                if card.card_type == "SkipCard" and len(skip_cards) < 2:
                    skip_cards.append(card)
        
        # Add Skip cards if needed
        while len(skip_cards) < 2:
            new_skip = SkipCard()
            if victim_state:
                victim_state.hand.append(new_skip)
            skip_cards.append(new_skip)
        
        # Set up actions
        attacker.set_actions([PlayCardAction(card=attack_card)])
        victim.set_actions([
            PlayCardAction(card=skip_cards[0]),
            PlayCardAction(card=skip_cards[1]),
        ])
        
        # Force turn order
        engine._turn_manager._turn_order = ["Attacker", "Victim"]
        engine._turn_manager._current_index = 0
        engine._turn_manager._turns_remaining = {"Attacker": 1, "Victim": 1}
        engine._state._turn_order = ["Attacker", "Victim"]
        engine._state._current_player_index = 0
        
        # Run attacker's turn
        engine._run_turn("Attacker")
        
        assert engine._turn_manager.get_turns_remaining("Victim") == 2
        
        # Run victim's first turn (Skip)
        engine._run_turn("Victim")
        
        assert engine._turn_manager.get_turns_remaining("Victim") == 1, \
            "Victim should have 1 turn after playing first Skip"
        
        # Run victim's second turn (Skip)
        engine._run_turn("Victim")
        
        assert engine._turn_manager.get_turns_remaining("Victim") == 0, \
            "Victim should have 0 turns after playing second Skip"
        
        # Verify skip events were recorded
        skip_events = engine.history.get_events_by_type(EventType.TURN_SKIPPED)
        assert len(skip_events) >= 2, "Should have at least 2 skip events"
    
    def test_attack_draw_then_play_drawn_skip(self) -> None:
        """
        When attacked, player can draw on turn 1 and play that card on turn 2.
        
        This is the key scenario: drawing a Skip on turn 1 and playing it on turn 2.
        
        Flow:
        1. Attacker plays Attack card
        2. Victim draws card (ends turn 1) - draws a Skip
        3. Victim plays the drawn Skip (ends turn 2)
        """
        engine: GameEngine = GameEngine(seed=42)
        
        attacker = ScriptedBot("Attacker")
        victim = ScriptedBot("Victim")
        
        engine.add_bot(attacker)
        engine.add_bot(victim)
        
        # Create deck where victim will draw Skip cards
        engine.create_deck({
            "AttackCard": 2,
            "SkipCard": 30,  # Make Skip cards very likely to draw
        })
        engine.setup_game(initial_hand_size=3)
        
        # Ensure attacker has Attack card
        attacker_state = engine._state.get_player("Attacker")
        attack_card: Card | None = None
        if attacker_state:
            for card in attacker_state.hand:
                if card.card_type == "AttackCard":
                    attack_card = card
                    break
        
        if attack_card is None:
            attack_card = AttackCard()
            if attacker_state:
                attacker_state.hand.append(attack_card)
        
        # Place a Skip card on top of the draw pile so victim draws it
        skip_to_draw = SkipCard()
        engine._state._draw_pile.append(skip_to_draw)
        
        # Force turn order
        engine._turn_manager._turn_order = ["Attacker", "Victim"]
        engine._turn_manager._current_index = 0
        engine._turn_manager._turns_remaining = {"Attacker": 1, "Victim": 1}
        engine._state._turn_order = ["Attacker", "Victim"]
        engine._state._current_player_index = 0
        
        # Attacker plays Attack
        attacker.set_actions([PlayCardAction(card=attack_card)])
        engine._run_turn("Attacker")
        
        assert engine._turn_manager.get_turns_remaining("Victim") == 2
        
        # Remember victim's hand size before drawing
        victim_state = engine._state.get_player("Victim")
        hand_size_before = len(victim_state.hand) if victim_state else 0
        
        # Victim draws on turn 1
        victim.set_actions([DrawCardAction()])
        engine._run_turn("Victim")
        
        # Verify victim drew a card
        hand_size_after = len(victim_state.hand) if victim_state else 0
        assert hand_size_after == hand_size_before + 1, \
            "Victim should have drawn 1 card"
        
        # Verify victim has 1 turn remaining
        assert engine._turn_manager.get_turns_remaining("Victim") == 1
        
        # Find the Skip card in victim's hand (should include the newly drawn one)
        skip_in_hand: Card | None = None
        if victim_state:
            for card in victim_state.hand:
                if card.card_type == "SkipCard":
                    skip_in_hand = card
                    break
        
        assert skip_in_hand is not None, \
            "Victim should have a Skip card in hand after drawing"
        
        # Victim plays Skip on turn 2
        victim.set_actions([PlayCardAction(card=skip_in_hand)])
        engine._run_turn("Victim")
        
        # Verify victim's turns are complete
        assert engine._turn_manager.get_turns_remaining("Victim") == 0, \
            "Victim should have 0 turns after playing Skip on turn 2"
    
    def test_attack_mixed_draw_and_skip(self) -> None:
        """
        Attacked player draws on turn 1, plays Skip on turn 2.
        
        Verifies each action counts as exactly 1 turn.
        """
        engine: GameEngine = GameEngine(seed=42)
        
        attacker = ScriptedBot("Attacker")
        victim = ScriptedBot("Victim")
        
        engine.add_bot(attacker)
        engine.add_bot(victim)
        
        engine.create_deck({
            "AttackCard": 5,
            "SkipCard": 20,
            "TacoCatCard": 20,
        })
        engine.setup_game(initial_hand_size=5)
        
        # Ensure attacker has Attack card
        attacker_state = engine._state.get_player("Attacker")
        attack_card: Card | None = None
        if attacker_state:
            for card in attacker_state.hand:
                if card.card_type == "AttackCard":
                    attack_card = card
                    break
        
        if attack_card is None:
            attack_card = AttackCard()
            if attacker_state:
                attacker_state.hand.append(attack_card)
        
        # Ensure victim has at least 1 Skip
        victim_state = engine._state.get_player("Victim")
        skip_card: Card | None = None
        if victim_state:
            for card in victim_state.hand:
                if card.card_type == "SkipCard":
                    skip_card = card
                    break
        
        if skip_card is None:
            skip_card = SkipCard()
            if victim_state:
                victim_state.hand.append(skip_card)
        
        # Force turn order
        engine._turn_manager._turn_order = ["Attacker", "Victim"]
        engine._turn_manager._current_index = 0
        engine._turn_manager._turns_remaining = {"Attacker": 1, "Victim": 1}
        engine._state._turn_order = ["Attacker", "Victim"]
        engine._state._current_player_index = 0
        
        attacker.set_actions([PlayCardAction(card=attack_card)])
        engine._run_turn("Attacker")
        
        # Victim has 2 turns
        assert engine._turn_manager.get_turns_remaining("Victim") == 2
        
        # Turn 1: Draw
        victim.set_actions([DrawCardAction()])
        engine._run_turn("Victim")
        assert engine._turn_manager.get_turns_remaining("Victim") == 1
        
        # Turn 2: Play Skip
        victim.set_actions([PlayCardAction(card=skip_card)])
        engine._run_turn("Victim")
        assert engine._turn_manager.get_turns_remaining("Victim") == 0
        
        # Check turn end events
        turn_ends = engine.history.get_events_by_type(EventType.TURN_END)
        victim_turn_ends = [e for e in turn_ends if e.player_id == "Victim"]
        assert len(victim_turn_ends) >= 2, \
            "Victim should have had at least 2 turn ends"
