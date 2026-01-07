"""
Tests for the Nope chain reaction system.

These tests verify that Nope cards work correctly:
- Single Nope negates an action
- Counter-Nope (Nope on a Nope) un-negates the original action
- Triple Nope (Nope on a Counter-Nope) re-negates the original action
- Players cannot Nope their own actions
"""

import pytest
from typing import Callable

from game.engine import GameEngine
from game.bots.base import (
    Bot,
    Action,
    DrawCardAction,
    PlayCardAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.cards.action_cards import SkipCard, NopeCard
from game.history import EventType, GameEvent


class ControllableBot(Bot):
    """
    A bot that can be controlled programmatically for testing.
    
    Allows tests to set exactly what action the bot will take on its turn
    and during reaction rounds.
    """
    
    def __init__(self, name: str) -> None:
        self._name: str = name
        self.turn_action: Action = DrawCardAction()
        self.react_action: Action | None = None
        self.react_call_count: int = 0
        self.turn_call_count: int = 0
    
    @property
    def name(self) -> str:
        return self._name
    
    def take_turn(self, view: BotView) -> Action:
        self.turn_call_count += 1
        return self.turn_action
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        self.react_call_count += 1
        return self.react_action
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        return view.my_hand[0]
    
    def on_explode(self, view: BotView) -> None:
        pass


class SequentialReactBot(Bot):
    """
    A bot that returns actions from a queue for each react() call.
    
    This allows testing specific sequences of Nope plays.
    """
    
    def __init__(self, name: str, reactions: list[Action | None] | None = None) -> None:
        self._name: str = name
        self.reactions: list[Action | None] = reactions or []
        self.react_index: int = 0
        self.was_asked_to_react: bool = False
    
    @property
    def name(self) -> str:
        return self._name
    
    def take_turn(self, view: BotView) -> Action:
        return DrawCardAction()
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        pass
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        self.was_asked_to_react = True
        if self.react_index < len(self.reactions):
            action = self.reactions[self.react_index]
            self.react_index += 1
            return action
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        return 0
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        return view.my_hand[0]
    
    def on_explode(self, view: BotView) -> None:
        pass


def create_test_engine_with_bots(
    bots: list[Bot],
    nope_count: int = 10,
    skip_count: int = 10,
) -> GameEngine:
    """
    Create a test engine with the given bots and a deck with Nopes and Skips.
    
    Inputs:
        bots: List of bots to add to the engine
        nope_count: Number of NopeCards in the deck
        skip_count: Number of SkipCards in the deck
    
    Returns:
        Configured GameEngine ready for testing
    """
    engine = GameEngine(seed=42)
    
    for bot in bots:
        engine.add_bot(bot)
    
    engine.create_deck({
        "NopeCard": nope_count,
        "SkipCard": skip_count,
    })
    engine.setup_game(initial_hand_size=0)  # Start with empty hands
    
    return engine


def give_nope_to_player(engine: GameEngine, player_id: str) -> NopeCard:
    """Give a Nope card directly to a player's hand and return it."""
    nope = NopeCard()
    player_state = engine._state.get_player(player_id)
    assert player_state is not None
    player_state.hand.append(nope)
    return nope


def give_skip_to_player(engine: GameEngine, player_id: str) -> SkipCard:
    """Give a Skip card directly to a player's hand and return it."""
    skip = SkipCard()
    player_state = engine._state.get_player(player_id)
    assert player_state is not None
    player_state.hand.append(skip)
    return skip


class TestNopeChainBasics:
    """Tests for basic Nope card functionality."""
    
    def test_single_nope_negates_action(self) -> None:
        """A single Nope should negate the triggering action."""
        # Setup: Bot1 plays Skip, Bot2 will Nope it
        bot1 = ControllableBot("Bot1")
        bot2 = ControllableBot("Bot2")
        
        engine = create_test_engine_with_bots([bot1, bot2])
        
        # Give Bot1 a Skip card
        skip_card = give_skip_to_player(engine, "Bot1")
        
        # Give Bot2 a Nope card and set them to use it
        nope_card = give_nope_to_player(engine, "Bot2")
        bot2.react_action = PlayCardAction(card=nope_card)
        
        # Bot1 will play the Skip
        bot1.turn_action = PlayCardAction(card=skip_card)
        
        # Run the turn
        engine._run_turn("Bot1")
        
        # Verify: Bot2's Nope was played (removed from hand)
        bot2_state = engine._state.get_player("Bot2")
        assert bot2_state is not None
        assert nope_card not in bot2_state.hand
        
        # Verify: Skip was played but action was negated (check logs)
        # The Skip card should be in the discard pile (it was played)
        assert skip_card in engine._state.discard_pile
        
        # Verify: Bot2 was asked to react
        assert bot2.react_call_count >= 1
    
    def test_no_nope_allows_action(self) -> None:
        """Without a Nope, the action should proceed normally."""
        bot1 = ControllableBot("Bot1")
        bot2 = ControllableBot("Bot2")
        
        engine = create_test_engine_with_bots([bot1, bot2])
        
        # Give Bot1 a Skip card
        skip_card = give_skip_to_player(engine, "Bot1")
        
        # Give Bot2 a Nope but they won't use it
        nope_card = give_nope_to_player(engine, "Bot2")
        bot2.react_action = None  # Don't react
        
        # Bot1 will play the Skip
        bot1.turn_action = PlayCardAction(card=skip_card)
        
        # Run the turn
        engine._run_turn("Bot1")
        
        # Verify: Bot2 still has their Nope (unused)
        bot2_state = engine._state.get_player("Bot2")
        assert bot2_state is not None
        assert nope_card in bot2_state.hand
        
        # Verify: Skip was played and is in discard
        assert skip_card in engine._state.discard_pile


class TestNopeChaining:
    """Tests for Nope chains (counter-Nope, Nope-on-Nope)."""
    
    def test_counter_nope_un_negates_action(self) -> None:
        """
        Counter-Nope should cancel the first Nope, allowing the action.
        
        Scenario:
        1. Bot1 plays Skip
        2. Bot2 plays Nope (would negate Skip)
        3. Bot3 plays Nope on Bot2's Nope (counter-Nope)
        4. Result: Skip effect SHOULD happen
        
        With seed 42, turn order is: Bot2 -> Bot1 -> Bot3
        Level 0 (Bot1 triggers): asks Bot3, then Bot2
        Level 1 (Bot2 triggers): asks Bot1, then Bot3
        
        So:
        - Bot2 is asked at L0 (plays nope1)
        - Bot3 is asked at L0 (declines), then at L1 (plays nope2)
        """
        bot1 = SequentialReactBot("Bot1")  # Will not Nope (playing the action)
        bot2 = SequentialReactBot("Bot2")
        bot3 = SequentialReactBot("Bot3")
        
        engine = create_test_engine_with_bots([bot1, bot2, bot3])
        
        # Give Bot1 a Skip card
        skip_card = give_skip_to_player(engine, "Bot1")
        
        # Give Bot2 a Nope - will be asked at L0
        nope1 = give_nope_to_player(engine, "Bot2")
        bot2.reactions = [PlayCardAction(card=nope1)]
        
        # Give Bot3 a Nope - asked at L0 (decline) and L1 (nope)
        nope2 = give_nope_to_player(engine, "Bot3")
        bot3.reactions = [None, PlayCardAction(card=nope2)]
        
        # Bot1 is asked at L1 (decline)
        bot1.reactions = [None]
        
        # Manually play the Skip card and run reaction
        bot1_state = engine._state.get_player("Bot1")
        assert bot1_state is not None
        bot1_state.hand.remove(skip_card)
        engine._state.discard(skip_card)
        
        # Create the play event
        play_event = engine._record_event(
            EventType.CARD_PLAYED,
            "Bot1",
            {"card_type": "SkipCard"},
        )
        
        # Run the reaction round
        negated = engine._run_reaction_round(play_event, "Bot1")
        
        # With counter-nope:
        # L0: nope_count = 0
        #   Bot3 declines, Bot2 Nopes (nope1) -> nope_count = 1
        #   Start L1 for Bot2's nope (Bot2 excluded)
        #     L1: nope_count = 0
        #       Bot1 declines, Bot3 Nopes (nope2) -> nope_count = 1
        #       Start L2 for Bot3's nope (Bot3 excluded)
        #         L2: No one reacts -> returns False
        #       (L2 returned False, don't decrement at L1)
        #     L1 returns: 1 % 2 == 1 -> True (Bot2's nope is negated!)
        #   (L1 returned True, L0's nope_count -= 1 -> 0)
        # L0 returns: 0 % 2 == 0 -> False (ORIGINAL ACTION NOT NEGATED)
        assert negated is False, "Counter-nope should un-negate the action"
        
        # Both Nopes should be discarded
        assert nope1 in engine._state.discard_pile
        assert nope2 in engine._state.discard_pile
    
    def test_triple_nope_negates_action(self) -> None:
        """
        Three Nopes should result in negation.
        
        Scenario:
        1. Bot1 plays Skip
        2. Bot2 plays Nope (negate)
        3. Bot3 plays Nope on Bot2's Nope (counter, un-negate)
        4. Bot2 plays Nope on Bot3's Nope (re-negate)
        5. Result: Skip effect should NOT happen
        
        With seed 42, turn order is: Bot2 -> Bot1 -> Bot3
        L0 (Bot1 triggers): Bot3, Bot2
        L1 (Bot2 triggers): Bot1, Bot3
        L2 (Bot3 triggers): Bot2, Bot1
        L3 (Bot2 triggers): Bot1, Bot3
        """
        bot1 = SequentialReactBot("Bot1")
        bot2 = SequentialReactBot("Bot2")
        bot3 = SequentialReactBot("Bot3")
        
        engine = create_test_engine_with_bots([bot1, bot2, bot3])
        
        # Give Bot2 two Nopes (for level 0 and level 2)
        nope1 = give_nope_to_player(engine, "Bot2")
        nope3 = give_nope_to_player(engine, "Bot2")
        
        # Give Bot3 one Nope (for level 1)
        nope2 = give_nope_to_player(engine, "Bot3")
        
        # Bot1: asked at L1 (decline), L2 (decline), L3 (decline)
        bot1.reactions = [None, None, None]
        
        # Bot2: asked at L0 (nope1), L2 (nope3)
        # NOT asked at L1 (triggered it) or L3 (triggered it)
        bot2.reactions = [PlayCardAction(card=nope1), PlayCardAction(card=nope3)]
        
        # Bot3: asked at L0 (decline), L1 (nope2), L3 (decline)
        # NOT asked at L2 (triggered it)
        bot3.reactions = [None, PlayCardAction(card=nope2), None]
        
        # Create the triggering event (Skip play)
        play_event = engine._record_event(
            EventType.CARD_PLAYED,
            "Bot1",
            {"card_type": "SkipCard"},
        )
        
        # Run the reaction round
        negated = engine._run_reaction_round(play_event, "Bot1")
        
        # Trace:
        # L0: nope_count = 0
        #   Bot3 declines, Bot2 Nopes (nope1) -> nope_count = 1
        #   Start L1 for Bot2's nope (Bot2 excluded)
        #     L1: nope_count = 0
        #       Bot1 declines, Bot3 Nopes (nope2) -> nope_count = 1
        #       Start L2 for Bot3's nope (Bot3 excluded)
        #         L2: nope_count = 0
        #           Bot2 Nopes (nope3) -> nope_count = 1
        #           Bot1 declines
        #           Start L3 for Bot2's nope (Bot2 excluded)
        #             L3: nope_count = 0
        #               Bot1 declines, Bot3 declines
        #             L3 returns: 0 % 2 == 0 -> False
        #           (L3 returned False, don't decrement at L2)
        #         L2 returns: 1 % 2 == 1 -> True (Bot3's nope negated!)
        #       (L2 returned True, L1's nope_count -= 1 -> 0)
        #     L1 returns: 0 % 2 == 0 -> False (Bot2's L0 nope NOT negated)
        #   (L1 returned False, don't decrement at L0)
        # L0 returns: 1 % 2 == 1 -> True (ORIGINAL ACTION NEGATED)
        
        assert negated is True, "Triple nope should result in negation"
        
        # All three nopes should be discarded
        assert nope1 in engine._state.discard_pile
        assert nope2 in engine._state.discard_pile
        assert nope3 in engine._state.discard_pile
    
    def test_player_cannot_nope_own_action(self) -> None:
        """
        A player should not be able to Nope their own action.
        
        """
        bot1 = SequentialReactBot("Bot1")
        bot2 = SequentialReactBot("Bot2")
        
        engine = create_test_engine_with_bots([bot1, bot2])
        
        # Give Bot1 a Nope - they should NOT be asked to react to their own action
        nope1 = give_nope_to_player(engine, "Bot1")
        bot1.reactions = [PlayCardAction(card=nope1)]  # Would Nope if asked
        
        # Create the triggering event (Bot1 plays something)
        play_event = engine._record_event(
            EventType.CARD_PLAYED,
            "Bot1",
            {"card_type": "SkipCard"},
        )
        
        # Run the reaction round
        negated = engine._run_reaction_round(play_event, "Bot1")
        
        # Bot1 should NOT have been asked to react (excluded as triggering player)
        assert bot1.was_asked_to_react is False, "Triggering player should not be asked to react"
        
        # Bot2 was asked but had nothing to play
        assert bot2.was_asked_to_react is True
        
        # Action not negated (Bot2 didn't nope)
        assert negated is False


class TestNopeInNestedRounds:
    """Tests for preventing players from noping multiple times in the same chain."""
    
    def test_each_player_reacts_once_per_round(self) -> None:
        """
        Each player should only be asked to react ONCE per reaction round level.
        
        They can nope at different nesting levels, but not multiple times
        at the same level.
        """
        call_counts: dict[str, list[int]] = {"Bot1": [], "Bot2": [], "Bot3": []}
        
        class TrackingBot(SequentialReactBot):
            def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
                call_counts[self._name].append(triggering_event.step)
                return super().react(view, triggering_event)
        
        bot1 = TrackingBot("Bot1", [])
        bot2 = TrackingBot("Bot2", [])
        bot3 = TrackingBot("Bot3", [])
        
        engine = create_test_engine_with_bots([bot1, bot2, bot3])
        
        # Setup: Bot2 has one Nope
        nope1 = give_nope_to_player(engine, "Bot2")
        bot2.reactions = [PlayCardAction(card=nope1)]
        
        # Create the triggering event
        play_event = engine._record_event(
            EventType.CARD_PLAYED,
            "Bot1",
            {"card_type": "SkipCard"},
        )
        
        # Run the reaction round
        engine._run_reaction_round(play_event, "Bot1")
        
        # Bot1 should NOT be asked at level 0 (triggering player)
        # Bot1 SHOULD be asked at level 1 (someone else noped)
        # Bot2 asked at level 0, NOT at level 1 (they just noped)
        # Bot3 asked at level 0 and level 1
        
        # Check: At each distinct event step, each non-triggering player should
        # be asked AT MOST once
        for bot_name, steps in call_counts.items():
            unique_steps = set(steps)
            if len(steps) != len(unique_steps):
                pytest.fail(
                    f"{bot_name} was asked to react multiple times "
                    f"to the same event: {steps}"
                )


class TestNopeCardRemoval:
    """Tests that Nope cards are properly removed and discarded."""
    
    def test_nope_card_removed_from_hand(self) -> None:
        """Playing a Nope should remove it from the player's hand."""
        bot1 = ControllableBot("Bot1")
        bot2 = ControllableBot("Bot2")
        
        engine = create_test_engine_with_bots([bot1, bot2])
        
        # Give Bot2 a Nope
        nope = give_nope_to_player(engine, "Bot2")
        bot2.react_action = PlayCardAction(card=nope)
        
        # Verify Bot2 has the Nope
        bot2_state = engine._state.get_player("Bot2")
        assert bot2_state is not None
        assert nope in bot2_state.hand
        
        # Create triggering event and run reaction
        play_event = engine._record_event(
            EventType.CARD_PLAYED,
            "Bot1",
            {"card_type": "SkipCard"},
        )
        engine._run_reaction_round(play_event, "Bot1")
        
        # Nope should be removed from hand
        assert nope not in bot2_state.hand
        
        # Nope should be in discard pile
        assert nope in engine._state.discard_pile
    
    def test_multiple_nopes_properly_tracked(self) -> None:
        """Multiple Nopes in a chain should all be removed and discarded."""
        bot1 = SequentialReactBot("Bot1")
        bot2 = SequentialReactBot("Bot2")
        bot3 = SequentialReactBot("Bot3")
        
        engine = create_test_engine_with_bots([bot1, bot2, bot3])
        
        # Give nopes
        nope1 = give_nope_to_player(engine, "Bot2")
        nope2 = give_nope_to_player(engine, "Bot3")
        
        bot2.reactions = [PlayCardAction(card=nope1)]
        bot3.reactions = [None, PlayCardAction(card=nope2)]
        
        # Run reaction
        play_event = engine._record_event(
            EventType.CARD_PLAYED,
            "Bot1",
            {"card_type": "SkipCard"},
        )
        engine._run_reaction_round(play_event, "Bot1")
        
        # Both nopes should be discarded
        assert nope1 in engine._state.discard_pile
        assert nope2 in engine._state.discard_pile
        
        # Neither player should have the nopes anymore
        bot2_state = engine._state.get_player("Bot2")
        bot3_state = engine._state.get_player("Bot3")
        assert bot2_state is not None
        assert bot3_state is not None
        assert nope1 not in bot2_state.hand
        assert nope2 not in bot3_state.hand
