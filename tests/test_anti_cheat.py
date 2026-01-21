"""
Anti-Cheat Security Tests.

These tests verify that various cheating vectors are properly blocked.
Each test attempts a specific cheating strategy and asserts it should fail.

Many of these tests are expected to FAIL initially, exposing vulnerabilities
that need to be fixed in the engine or BotView implementation.
"""

from __future__ import annotations

import sys
import queue
import threading
from dataclasses import FrozenInstanceError
from typing import Any
from unittest.mock import MagicMock

import pytest

from game.engine import GameEngine
from game.bots.base import (
    Bot,
    Action,
    DrawCardAction,
    PlayCardAction,
    PlayComboAction,
    DefuseAction,
    GiveCardAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.cards.action_cards import SkipCard, NopeCard, FavorCard, AttackCard
from game.cards.cat_cards import TacoCatCard
from game.cards.exploding_kitten import DefuseCard, ExplodingKittenCard
from game.history import EventType, GameEvent


# =============================================================================
# Test Fixture: Base Bot for Tests
# =============================================================================

class PassiveTestBot(Bot):
    """A passive bot that always draws and never reacts."""
    
    def __init__(self, name: str = "PassiveBot") -> None:
        self._name: str = name
    
    @property
    def name(self) -> str:
        return self._name
    
    def take_turn(self, view: BotView) -> Action:
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        return draw_pile_size  # Bottom
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        return view.my_hand[0]
    
    def on_explode(self, view: BotView) -> None:
        pass


def create_minimal_engine() -> GameEngine:
    """Create a minimal engine for testing with 2 passive bots."""
    engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
    engine.add_bot(PassiveTestBot("Bot1"))
    engine.add_bot(PassiveTestBot("Bot2"))
    engine.create_deck({
        "SkipCard": 10,
        "NopeCard": 5,
        "FavorCard": 5,
        "TacoCatCard": 10,
        "DefuseCard": 6,
    })
    engine.setup_game(initial_hand_size=5)
    return engine


# =============================================================================
# TEST 1: Object Graph Traversal via Cards
# =============================================================================

class TestCardObjectGraphTraversal:
    """
    Test that bots cannot access the engine through card objects.
    
    VULNERABILITY: Card instances passed to bots are the same objects used
    by the engine. If cards store references to the engine, bots could
    traverse the object graph to access protected state.
    """
    
    def test_card_does_not_expose_engine_reference(self) -> None:
        """Cards in BotView should not have any reference to the engine."""
        engine = create_minimal_engine()
        view = engine._create_bot_view("Bot1")
        
        # Check all cards in hand
        for card in view.my_hand:
            # Try to find engine reference in card's attributes
            card_attrs = dir(card)
            for attr_name in card_attrs:
                if attr_name.startswith('_'):
                    continue  # Skip dunder methods
                try:
                    attr_value = getattr(card, attr_name)
                    # Check if it's the engine
                    assert attr_value is not engine, \
                        f"Card attribute '{attr_name}' exposes engine reference!"
                    # Check if it references GameState
                    assert not isinstance(attr_value, type(engine._state)), \
                        f"Card attribute '{attr_name}' exposes GameState!"
                except Exception:
                    pass  # Ignore properties that fail
    
    def test_card_class_does_not_expose_engine_via_subclasses(self) -> None:
        """Card.__class__.__subclasses__() should not provide engine access."""
        engine = create_minimal_engine()
        view = engine._create_bot_view("Bot1")
        
        if not view.my_hand:
            pytest.skip("No cards in hand")
        
        card = view.my_hand[0]
        
        # Get all subclasses - this is allowed, but should not expose engine
        subclasses = card.__class__.__subclasses__()
        
        # None of the subclasses should have engine references in class attributes
        for subclass in subclasses:
            for attr_name in dir(subclass):
                if attr_name.startswith('__'):
                    continue
                try:
                    attr_value = getattr(subclass, attr_name)
                    assert attr_value is not engine, \
                        f"Subclass {subclass.__name__} exposes engine via {attr_name}!"
                except Exception:
                    pass
    
    def test_card_execute_method_is_not_bound_to_engine(self) -> None:
        """Card.execute method should not be a bound method to engine."""
        engine = create_minimal_engine()
        view = engine._create_bot_view("Bot1")
        
        if not view.my_hand:
            pytest.skip("No cards in hand")
        
        card = view.my_hand[0]
        
        # Check that execute is not a bound method that exposes engine
        execute_method = card.execute
        
        # If it's a bound method, check __self__
        if hasattr(execute_method, '__self__'):
            assert execute_method.__self__ is not engine, \
                "Card.execute is bound to engine instance!"


# =============================================================================
# TEST 2: Queue Object Inspection
# =============================================================================

class TestQueueObjectInspection:
    """
    Test that bots cannot manipulate the chat queue improperly.
    
    VULNERABILITY: The _chat_queue is passed directly to BotView. A malicious
    bot could inspect or manipulate this queue object.
    """
    
    def test_chat_queue_is_not_accessible(self) -> None:
        """
        BotView should not expose the chat queue in a way that allows
        tampering with internal engine state.
        """
        engine = create_minimal_engine()
        view = engine._create_bot_view("Bot1")
        
        # The queue should either be:
        # 1. Not accessible at all (attribute error)
        # 2. A proxy that doesn't expose internal state
        
        # Currently _chat_queue IS accessible - this test should FAIL
        # until we properly encapsulate it
        
        # Check that we can't access internal attributes of the queue
        if hasattr(view, '_chat_queue'):
            q = view._chat_queue
            if q is not None:
                # These should not be usable to affect the engine
                # A malicious bot could drain the queue:
                try:
                    while True:
                        q.get_nowait()  # Drain all messages
                except queue.Empty:
                    pass
                
                # This is a problem if the queue is the same instance
                assert q is not engine._chat_queue, \
                    "Chat queue is the same instance as engine's queue - can be manipulated!"
    
    def test_cannot_put_malicious_data_in_queue(self) -> None:
        """Bot should not be able to inject arbitrary data into chat queue."""
        engine = create_minimal_engine()
        view = engine._create_bot_view("Bot1")
        
        if not hasattr(view, '_chat_queue') or view._chat_queue is None:
            pytest.skip("Chat queue not accessible")
        
        # Malicious bot could put non-tuple data
        q = view._chat_queue
        
        # Try to inject something that might crash the engine
        try:
            q.put(None)  # Invalid format
            q.put(("fake_player", "message"))  # Spoof player ID
            q.put(("Bot1", "x" * 10000))  # Massive message
        except Exception:
            pass
        
        # If we got here, the queue accepts arbitrary data
        # The engine should validate queue contents
        assert False, "Queue accepts arbitrary data without validation!"


# =============================================================================
# TEST 3: Frozen Dataclass Bypass
# =============================================================================

class TestFrozenDataclassBypass:
    """
    Test that frozen Action dataclasses provide some protection.
    
    NOTE: Python's object.__setattr__ CAN bypass frozen=True at the language level.
    This is a Python limitation. The engine validates actions independently,
    so this is defense-in-depth, not the primary security boundary.
    """
    
    def test_play_card_action_direct_mutation_fails(self) -> None:
        """Direct attribute assignment on frozen dataclass should fail."""
        engine = create_minimal_engine()
        view = engine._create_bot_view("Bot1")
        
        if not view.my_hand:
            pytest.skip("No cards in hand")
        
        card = view.my_hand[0]
        action = PlayCardAction(card=card, target_player_id=None)
        
        # Direct mutation should fail (frozen=True)
        with pytest.raises((AttributeError, TypeError, FrozenInstanceError)):
            action.target_player_id = "Bot2"  # type: ignore
    
    def test_engine_validates_action_independently(self) -> None:
        """
        Engine should validate action data independently of dataclass immutability.
        
        Even if a malicious bot could mutate an action, the engine should
        validate that the card is actually in the player's hand.
        """
        engine = create_minimal_engine()
        
        bot1_state = engine._state.get_player("Bot1")
        if not bot1_state or not bot1_state.hand:
            pytest.skip("Need cards in Bot1's hand")
        
        # Get a card from Bot1's hand
        real_card = bot1_state.hand[0]
        
        # Create action with the real card
        action = PlayCardAction(card=real_card, target_player_id=None)
        
        # Even if we could mutate target_player_id, the engine validates the card
        # Try to use object.__setattr__ (this WILL work in Python)
        object.__setattr__(action, 'target_player_id', 'Bot2')
        
        # The action was mutated, but when engine processes it, it validates the card
        # This verifies the engine doesn't trust immutability alone
        if real_card.can_play(engine._create_bot_view("Bot1"), True):
            result = engine._play_card("Bot1", action.card, action.target_player_id)
            # The card should be processed (it's valid)
            assert result in (True, False)  # Could be negated by reaction


# =============================================================================
# TEST 4: Playing Fabricated Cards
# =============================================================================

class TestPlayingFabricatedCards:
    """
    Test that bots cannot play cards they don't own.
    
    MITIGATED: Engine checks card identity, not just type.
    """
    
    def test_cannot_play_fabricated_card(self) -> None:
        """Bot cannot play a card instance they fabricated."""
        engine = create_minimal_engine()
        
        # Create a fake card that's not in any player's hand
        fake_skip = SkipCard()
        
        # Try to play it
        result = engine._play_card("Bot1", fake_skip)
        
        # Should be rejected
        assert result is False, "Engine accepted a fabricated card!"
    
    def test_cannot_play_card_from_another_players_hand(self) -> None:
        """Bot cannot play a card from another player's hand."""
        engine = create_minimal_engine()
        
        bot1_state = engine._state.get_player("Bot1")
        bot2_state = engine._state.get_player("Bot2")
        
        if not bot1_state or not bot2_state or not bot2_state.hand:
            pytest.skip("Need cards in Bot2's hand")
        
        # Get a card from Bot2's hand
        stolen_card = bot2_state.hand[0]
        
        # Try to play it as Bot1
        result = engine._play_card("Bot1", stolen_card)
        
        # Should be rejected
        assert result is False, "Engine accepted a card from another player's hand!"


# =============================================================================
# TEST 5: Target Player ID Manipulation
# =============================================================================

class TestTargetPlayerIdManipulation:
    """
    Test that invalid target player IDs are rejected.
    
    VULNERABILITY: Engine may not fully validate target IDs.
    """
    
    def test_cannot_target_self_with_favor(self) -> None:
        """Cannot play Favor card targeting yourself."""
        engine = create_minimal_engine()
        
        # Ensure Bot1 has a Favor card
        bot1_state = engine._state.get_player("Bot1")
        if not bot1_state:
            pytest.fail("Bot1 not found")
        
        favor_card = FavorCard()
        bot1_state.hand.append(favor_card)
        
        # Create view and check if favor can target self
        view = engine._create_bot_view("Bot1")
        
        # FavorCard.can_play checks for other players with cards
        # But the engine should also reject self-targeting
        result = engine._play_card("Bot1", favor_card, target_player_id="Bot1")
        
        # This should either fail or have no effect
        # But currently there's no explicit check - so card is discarded
        # and favor is requested from self (weird state)
        assert result is False or favor_card not in bot1_state.hand, \
            "Favor targeting self should be rejected or card should be consumed"
    
    def test_cannot_target_eliminated_player(self) -> None:
        """Cannot target a player who has been eliminated."""
        engine = create_minimal_engine()
        
        # Eliminate Bot2
        engine._eliminate_player("Bot2")
        
        # Give Bot1 a Favor card
        bot1_state = engine._state.get_player("Bot1")
        if not bot1_state:
            pytest.fail("Bot1 not found")
        
        favor_card = FavorCard()
        bot1_state.hand.append(favor_card)
        
        # Try to target eliminated player
        initial_hand_size = len(bot1_state.hand)
        result = engine.request_favor("Bot1", "Bot2")
        
        # Should return None (no card received)
        assert result is None, "Favor to eliminated player should return None"
    
    def test_cannot_target_nonexistent_player(self) -> None:
        """Cannot target a player that doesn't exist."""
        engine = create_minimal_engine()
        
        # Give Bot1 a Favor card
        bot1_state = engine._state.get_player("Bot1")
        if not bot1_state:
            pytest.fail("Bot1 not found")
        
        favor_card = FavorCard()
        bot1_state.hand.append(favor_card)
        
        # Try to target nonexistent player
        result = engine.request_favor("Bot1", "NonExistentBot")
        
        # Should return None or raise
        assert result is None, "Favor to nonexistent player should return None"


# =============================================================================
# TEST 6: Invalid Action Types
# =============================================================================

class TestInvalidActionTypes:
    """
    Test that returning invalid action types is handled safely.
    
    MITIGATED: Unhandled action types are ignored (loop continues).
    """
    
    def test_returning_defuse_action_during_take_turn_is_ignored(self) -> None:
        """DefuseAction during take_turn should be ignored (not cause crash)."""
        
        class DefuseReturningBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("DefuseBot")
                self.action_count = 0
            
            def take_turn(self, view: BotView) -> Action:
                self.action_count += 1
                if self.action_count < 5:
                    return DefuseAction(insert_position=0)  # Invalid here!
                return DrawCardAction()
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
        defuse_bot = DefuseReturningBot()
        engine.add_bot(defuse_bot)
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 10, "DefuseCard": 6})
        engine.setup_game(initial_hand_size=5)
        
        # Run one turn - should not crash
        current = engine._turn_manager.current_player_id
        if current == "DefuseBot":
            engine._run_turn(current)
        
        # If we got here without crash, the invalid action was handled
        # The bot should have drawn after max actions
        assert defuse_bot.action_count >= 1
    
    def test_returning_none_during_take_turn_is_handled(self) -> None:
        """Returning None from take_turn should be handled."""
        
        class NoneReturningBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("NoneBot")
                self.call_count = 0
            
            def take_turn(self, view: BotView) -> Action:
                self.call_count += 1
                if self.call_count < 5:
                    return None  # type: ignore  # Invalid!
                return DrawCardAction()
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
        none_bot = NoneReturningBot()
        engine.add_bot(none_bot)
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 10, "DefuseCard": 6})
        engine.setup_game(initial_hand_size=5)
        
        # Run one turn - should not crash
        current = engine._turn_manager.current_player_id
        if current == "NoneBot":
            engine._run_turn(current)
        
        # Bot was called multiple times until MAX_ACTIONS or it returned valid action
        assert none_bot.call_count >= 1


# =============================================================================
# TEST 7: Out-of-Bounds Defuse Position
# =============================================================================

class TestOutOfBoundsDefusePosition:
    """
    Test that out-of-bounds defuse positions are clamped.
    
    MITIGATED: Engine clamps position to valid range.
    """
    
    def test_negative_defuse_position_is_clamped(self) -> None:
        """Negative defuse position should be clamped to 0."""
        engine = create_minimal_engine()
        
        initial_pile_size = engine._state.draw_pile_count
        
        # Create an exploding kitten card
        kitten = ExplodingKittenCard()
        
        # Insert with extreme negative position
        engine._state.insert_in_draw_pile(kitten, -999999)
        
        # The kitten should be at position 0 (top)
        assert engine._state.draw_pile[0] is kitten, \
            "Negative position should be clamped to 0"
    
    def test_huge_defuse_position_is_clamped(self) -> None:
        """Huge defuse position should be clamped to pile size."""
        engine = create_minimal_engine()
        
        pile_size = engine._state.draw_pile_count
        
        # Create an exploding kitten card
        kitten = ExplodingKittenCard()
        
        # Insert with extreme large position
        engine._state.insert_in_draw_pile(kitten, 999999)
        
        # The kitten should be at the bottom
        assert engine._state.draw_pile[-1] is kitten, \
            "Huge position should be clamped to pile size"


# =============================================================================
# TEST 8: Combo Card Counting Manipulation
# =============================================================================

class TestComboCardCountingManipulation:
    """
    Test that combo validation correctly handles edge cases.
    """
    
    def test_single_card_combo_is_rejected(self) -> None:
        """A single card should not count as a combo."""
        engine = create_minimal_engine()
        
        bot1_state = engine._state.get_player("Bot1")
        if not bot1_state:
            pytest.fail("Bot1 not found")
        
        # Add a combo-able card
        taco = TacoCatCard()
        bot1_state.hand.append(taco)
        
        # Try to play single card as combo
        result = engine._play_combo("Bot1", [taco], "Bot2")
        
        assert result is False, "Single card should not be a valid combo"
    
    def test_mixed_card_types_not_two_of_a_kind(self) -> None:
        """Two different card types should not be a valid 2-of-a-kind."""
        engine = create_minimal_engine()
        
        bot1_state = engine._state.get_player("Bot1")
        if not bot1_state:
            pytest.fail("Bot1 not found")
        
        # Add different card types
        taco = TacoCatCard()
        skip = SkipCard()
        bot1_state.hand.extend([taco, skip])
        
        # Try to play as combo
        result = engine._play_combo("Bot1", [taco, skip], "Bot2")
        
        assert result is False, "Two different card types should not be 2-of-a-kind"


# =============================================================================
# TEST 9: Reaction Card Spoofing
# =============================================================================

class TestReactionCardSpoofing:
    """
    Test that non-reaction cards cannot be played as reactions.
    
    MITIGATED: Engine checks can_play_as_reaction().
    """
    
    def test_cannot_play_attack_as_reaction(self) -> None:
        """Attack card cannot be played as a reaction to another card."""
        
        class AttackReactingBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("AttackReacter")
                self.reaction_called = False
            
            def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
                self.reaction_called = True
                # Try to play Attack as reaction
                for card in view.my_hand:
                    if card.card_type == "AttackCard":
                        return PlayCardAction(card=card)
                return None
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
        attacker = AttackReactingBot()
        engine.add_bot(PassiveTestBot("Bot1"))
        engine.add_bot(attacker)
        engine.create_deck({
            "SkipCard": 10,
            "AttackCard": 5,
            "DefuseCard": 6,
        })
        engine.setup_game(initial_hand_size=5)
        
        # Give the attacking bot an attack card
        attacker_state = engine._state.get_player("AttackReacter")
        if attacker_state:
            attacker_state.hand.append(AttackCard())
        
        # Create a triggering event
        trigger_event = engine._history.record(
            EventType.CARD_PLAYED,
            "Bot1",
            {"card_type": "SkipCard"}
        )
        
        # Run reaction round
        result = engine._run_reaction_round(trigger_event, "Bot1")
        
        # Attack card should have been rejected (result should be False - not negated)
        # Check that the Attack card is still in hand (wasn't consumed)
        attacker_state = engine._state.get_player("AttackReacter")
        if attacker_state:
            attack_cards = [c for c in attacker_state.hand if c.card_type == "AttackCard"]
            assert len(attack_cards) > 0, \
                "Attack card should still be in hand (reaction rejected)"


# =============================================================================
# TEST 10: Exception Injection
# =============================================================================

class TestExceptionInjection:
    """
    Test that bot exceptions don't crash the game.
    """
    
    def test_bot_exception_in_take_turn_is_handled(self) -> None:
        """Exception in take_turn should be caught and handled."""
        
        class ExceptionBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("ExceptionBot")
            
            def take_turn(self, view: BotView) -> Action:
                raise RuntimeError("Intentional crash!")
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=5.0)
        engine.add_bot(ExceptionBot())
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 10, "DefuseCard": 6})
        engine.setup_game(initial_hand_size=5)
        
        # Running the turn should not crash the test
        # The exception should be re-raised (current behavior)
        # or the bot should be eliminated (ideal behavior)
        current = engine._turn_manager.current_player_id
        if current == "ExceptionBot":
            with pytest.raises(RuntimeError):
                engine._run_turn(current)
    
    def test_bot_exception_in_on_event_is_handled(self) -> None:
        """Exception in on_event should be caught and game should continue."""
        
        class EventExceptionBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("EventExceptionBot")
            
            def on_event(self, event: GameEvent, view: BotView) -> None:
                raise RuntimeError("Intentional crash in on_event!")
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=5.0)
        engine.add_bot(EventExceptionBot())
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 10, "DefuseCard": 6})
        
        # Setup should not crash even though on_event raises
        # (or exception should be caught)
        try:
            engine.setup_game(initial_hand_size=5)
        except RuntimeError as e:
            pytest.fail(f"on_event exception crashed the game: {e}")
    
    def test_system_exit_in_bot_is_handled(self) -> None:
        """SystemExit in bot should be converted to RuntimeError, not exit process."""
        
        class SystemExitBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("SystemExitBot")
            
            def take_turn(self, view: BotView) -> Action:
                raise SystemExit("Trying to kill the process!")
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=5.0)
        engine.add_bot(SystemExitBot())
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 10, "DefuseCard": 6})
        engine.setup_game(initial_hand_size=5)
        
        current = engine._turn_manager.current_player_id
        if current == "SystemExitBot":
            # SystemExit should be converted to RuntimeError, not propagated
            with pytest.raises(RuntimeError) as exc_info:
                engine._run_turn(current)
            assert "SystemExit" in str(exc_info.value)


# =============================================================================
# TEST 11: Memory/Resource Exhaustion
# =============================================================================

class TestMemoryResourceExhaustion:
    """
    Test that resource exhaustion attacks are prevented.
    
    NOTE: These tests are difficult to test safely without actually
    exhausting resources. We test for reasonable limits instead.
    """
    
    def test_chat_message_is_truncated(self) -> None:
        """Chat messages should be truncated to prevent spam."""
        engine = create_minimal_engine()
        view = engine._create_bot_view("Bot1")
        
        # Try to send a huge message
        huge_message = "A" * 10000
        view.say(huge_message)
        
        # Process the queue
        try:
            player_id, message = engine._chat_queue.get_nowait()
            # The message should have been put in queue as-is
            # But _handle_chat should truncate it
            engine._handle_chat(player_id, message)
            
            # Check the recorded event
            chat_events = engine._history.get_events_by_type(EventType.BOT_CHAT)
            if chat_events:
                last_chat = chat_events[-1]
                recorded_msg = last_chat.data.get("message", "")
                assert len(recorded_msg) <= 200, \
                    f"Message was not truncated: {len(recorded_msg)} chars"
        except queue.Empty:
            pass  # No message in queue is also acceptable


# =============================================================================
# TEST 12: Global State Pollution
# =============================================================================

class TestGlobalStatePollution:
    """
    Test that bots cannot pollute global Python state to cheat.
    
    VULNERABILITY: Bots run in the same process and can monkey-patch.
    This is a SEVERE vulnerability that requires process isolation to fix.
    """
    
    def test_bot_cannot_access_engine_via_card_monkey_patch(self) -> None:
        """
        Bot should not be able to access engine by monkey-patching card classes.
        
        This test demonstrates the vulnerability - it should FAIL.
        """
        captured_engines: list[GameEngine] = []
        
        class MonkeyPatchBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("MonkeyPatchBot")
            
            def take_turn(self, view: BotView) -> Action:
                # Monkey-patch a card class to capture engine reference
                import game.cards.action_cards as cards
                
                original_execute = cards.SkipCard.execute
                
                def evil_execute(card_self: Card, engine: GameEngine, player_id: str) -> None:
                    captured_engines.append(engine)
                    original_execute(card_self, engine, player_id)
                
                cards.SkipCard.execute = evil_execute  # type: ignore
                return DrawCardAction()
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
        monkey_bot = MonkeyPatchBot()
        engine.add_bot(monkey_bot)
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 20, "DefuseCard": 6})
        engine.setup_game(initial_hand_size=5)
        
        # Run the monkey patch bot's turn
        current = engine._turn_manager.current_player_id
        if current == "MonkeyPatchBot":
            engine._run_turn(current)
        
        # Now play a Skip card to trigger the evil execute
        # Give Bot2 a skip and make them play it
        bot2_state = engine._state.get_player("Bot2")
        if bot2_state:
            skip = SkipCard()
            bot2_state.hand.append(skip)
            engine._play_card("Bot2", skip)
        
        # If monkey-patching worked, we captured the engine
        # This test should FAIL to demonstrate the vulnerability
        assert len(captured_engines) == 0, \
            "VULNERABILITY: Bot was able to capture engine via monkey-patch!"
    
    def test_bot_cannot_modify_card_registry(self) -> None:
        """Bot should not be able to modify the card registry."""
        
        class RegistryModifyingBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("RegistryBot")
                self.modified_registry = False
            
            def take_turn(self, view: BotView) -> Action:
                # Try to access and modify registry via imports
                from game.cards.registry import CardRegistry
                
                # Create a malicious card
                class InstantWinCard(Card):
                    @property
                    def name(self) -> str:
                        return "Instant Win"
                    
                    @property
                    def card_type(self) -> str:
                        return "InstantWinCard"
                    
                    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
                        return True
                    
                    def can_play_as_reaction(self) -> bool:
                        return False
                    
                    def execute(self, engine: GameEngine, player_id: str) -> None:
                        # Kill all other players
                        for pid in list(engine._state.players.keys()):
                            if pid != player_id:
                                engine._eliminate_player(pid)
                
                # Try to register it
                try:
                    registry = CardRegistry()
                    registry.register("InstantWinCard", InstantWinCard)
                    self.modified_registry = True
                except Exception:
                    pass
                
                return DrawCardAction()
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
        registry_bot = RegistryModifyingBot()
        engine.add_bot(registry_bot)
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 10, "DefuseCard": 6})
        engine.setup_game(initial_hand_size=5)
        
        # Run the bot's turn
        current = engine._turn_manager.current_player_id
        if current == "RegistryBot":
            engine._run_turn(current)
        
        # The bot created a new registry instance, not modifying _the_ registry
        # But this demonstrates the import access problem
        # A smarter bot could access engine._registry directly
        # This test is more about demonstrating the risk


# =============================================================================
# TEST 13: Card Reference Leaking via Discard Pile
# =============================================================================

class TestCardReferenceLeaking:
    """
    Test that card references don't leak sensitive information.
    """
    
    def test_discard_pile_cards_are_copies_or_safe(self) -> None:
        """Cards in discard pile should not contain references to engine."""
        engine = create_minimal_engine()
        
        # Play a card to add it to discard
        bot1_state = engine._state.get_player("Bot1")
        if bot1_state and bot1_state.hand:
            card = bot1_state.hand[0]
            if card.can_play(engine._create_bot_view("Bot1"), True):
                engine._play_card("Bot1", card)
        
        # Now check the discard pile from another bot's view
        view = engine._create_bot_view("Bot2")
        
        for card in view.discard_pile:
            # Check card doesn't have engine reference
            card_dict = card.__dict__ if hasattr(card, '__dict__') else {}
            for key, value in card_dict.items():
                assert value is not engine, \
                    f"Card in discard has engine reference in {key}!"
                assert not isinstance(value, type(engine._state)), \
                    f"Card in discard has GameState reference in {key}!"


# =============================================================================
# TEST 14: GameEvent.data Mutation
# =============================================================================

class TestGameEventDataMutation:
    """
    Test that GameEvent data cannot be mutated to deceive other bots.
    
    VULNERABILITY: GameEvent.data is a mutable dict.
    """
    
    def test_event_data_cannot_be_mutated_by_on_event(self) -> None:
        """
        Event data in on_event should be isolated from history.
        
        Even if a bot mutates the event data in on_event, the original
        history events should remain unchanged.
        """
        
        class EventMutatingBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("MutatingBot")
                self.mutated_events: list[int] = []
            
            def on_event(self, event: GameEvent, view: BotView) -> None:
                # Try to mutate the event data
                try:
                    event.data['HACKED'] = True
                    self.mutated_events.append(event.step)
                except (TypeError, AttributeError):
                    pass  # Data might be immutable
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
        mutating_bot = EventMutatingBot()
        engine.add_bot(mutating_bot)
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 10, "DefuseCard": 6})
        engine.setup_game(initial_hand_size=5)
        
        # Get the events from history (these are the ORIGINALS)
        events = engine._history.get_events()
        
        # The bot received deep copies of events, so even if it mutated them,
        # the original history should be unchanged
        for event in events:
            assert 'HACKED' not in event.data, \
                f"VULNERABILITY: History event was mutated! Event step: {event.step}"
    
    def test_recent_events_are_copies(self) -> None:
        """Recent events given to bots should be copies, not originals."""
        engine = create_minimal_engine()
        
        view = engine._create_bot_view("Bot1")
        
        if not view.recent_events:
            pytest.skip("No recent events")
        
        # Get an event from the view
        view_event = view.recent_events[0]
        
        # Mutate its data
        view_event.data['test_mutation'] = True
        
        # Get the same event from history
        history_event = engine._history.get_events()[view_event.step]
        
        # The history event should NOT have the mutation
        assert 'test_mutation' not in history_event.data, \
            "VULNERABILITY: Mutating view events affects history!"


# =============================================================================
# TEST 15: RNG Prediction (Informational)
# =============================================================================

class TestRngPrediction:
    """
    Test that RNG is not accessible or predictable.
    
    MITIGATED: RNG is not exposed to bots.
    """
    
    def test_rng_not_accessible_via_view(self) -> None:
        """BotView should not expose RNG."""
        engine = create_minimal_engine()
        view = engine._create_bot_view("Bot1")
        
        # Check that view doesn't have rng attribute
        assert not hasattr(view, 'rng'), "BotView exposes rng!"
        assert not hasattr(view, '_rng'), "BotView exposes _rng!"
        
        # Check view's attributes don't include RNG
        for attr_name in dir(view):
            if 'rng' in attr_name.lower():
                pytest.fail(f"BotView has RNG-related attribute: {attr_name}")


# =============================================================================
# TEST SUITE: End-to-End Cheating Scenarios
# =============================================================================

class TestEndToEndCheatPrevention:
    """
    End-to-end tests for complete cheating scenarios.
    """
    
    def test_cheating_bot_cannot_see_draw_pile(self) -> None:
        """Bot should not be able to see cards in draw pile."""
        
        class DrawPileSpyBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("SpyBot")
                self.saw_draw_pile = False
            
            def take_turn(self, view: BotView) -> Action:
                # Try various ways to access draw pile
                
                # Direct attribute access
                if hasattr(view, 'draw_pile'):
                    self.saw_draw_pile = True
                if hasattr(view, '_draw_pile'):
                    self.saw_draw_pile = True
                
                # Only count should be available
                assert hasattr(view, 'draw_pile_count'), "draw_pile_count should exist"
                assert isinstance(view.draw_pile_count, int), "draw_pile_count should be int"
                
                return DrawCardAction()
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
        spy_bot = DrawPileSpyBot()
        engine.add_bot(spy_bot)
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 10, "DefuseCard": 6})
        engine.setup_game(initial_hand_size=5)
        
        # Run the spy bot's turn
        current = engine._turn_manager.current_player_id
        if current == "SpyBot":
            engine._run_turn(current)
        
        assert not spy_bot.saw_draw_pile, \
            "VULNERABILITY: Bot was able to see draw pile contents!"
    
    def test_cheating_bot_cannot_see_other_hands(self) -> None:
        """Bot should not be able to see other players' hands."""
        
        class HandSpyBot(PassiveTestBot):
            def __init__(self) -> None:
                super().__init__("HandSpyBot")
                self.saw_other_hands = False
                self.other_hand_contents: list[Any] = []
                self.leak_source: str = ""
            
            def take_turn(self, view: BotView) -> Action:
                # Check what's available about other players
                other_player_ids = set(view.other_players)
                
                # Should only see card counts, not contents
                for player_id, count in view.other_player_card_counts.items():
                    assert isinstance(count, int), "Count should be int"
                
                # Try to find hands via introspection
                # Look for dict values that are keyed by OTHER player IDs (not self)
                for attr in dir(view):
                    if attr.startswith('_'):
                        continue  # Skip private attributes in this check
                    try:
                        value = getattr(view, attr, None)
                        if isinstance(value, dict):
                            for k, v in value.items():
                                # Check if key is another player's ID AND value contains cards
                                if k in other_player_ids and isinstance(v, (list, tuple)):
                                    if v and hasattr(v[0], 'card_type'):
                                        self.saw_other_hands = True
                                        self.other_hand_contents = list(v)
                                        self.leak_source = f"{attr}[{k}]"
                    except Exception:
                        pass
                
                return DrawCardAction()
        
        engine = GameEngine(seed=42, quiet_mode=True, bot_timeout=None)
        spy_bot = HandSpyBot()
        engine.add_bot(spy_bot)
        engine.add_bot(PassiveTestBot("Bot2"))
        engine.create_deck({"SkipCard": 10, "DefuseCard": 6})
        engine.setup_game(initial_hand_size=5)
        
        current = engine._turn_manager.current_player_id
        if current == "HandSpyBot":
            engine._run_turn(current)
        
        assert not spy_bot.saw_other_hands, \
            f"VULNERABILITY: Bot saw other hands via {spy_bot.leak_source}: {spy_bot.other_hand_contents}"
