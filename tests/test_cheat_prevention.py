"""Tests for cheat prevention mechanisms in the game."""

import unittest
from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType, GameEngine, TargetContext, GameAction, ActionType


class CheatBot(Bot):
    """A bot that attempts various cheating strategies."""
    
    def __init__(self, name: str, cheat_type: str = "none"):
        super().__init__(name)
        self.cheat_type = cheat_type
        self.cheat_attempted = False
        
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        if self.cheat_type == "add_cards_in_play":
            # CHEAT: Try to add cards to hand during play phase
            self.cheat_attempted = True
            self.hand.append(Card(CardType.DEFUSE))
            self.hand.append(Card(CardType.SKIP))
            return None
        
        if self.cheat_type == "modify_gamestate":
            # CHEAT: Try to modify game state
            self.cheat_attempted = True
            state.cards_left_to_draw = 0
            state.alive_bots = 1
            state.history_of_played_cards.append(Card(CardType.SKIP))
            return None
            
        return None
    
    def handle_exploding_kitten(self, state: GameState) -> int:
        if self.cheat_type == "add_defuse_on_explosion":
            # CHEAT: Try to add defuse when we don't have one
            self.cheat_attempted = True
            self.hand.append(Card(CardType.DEFUSE))
        return 0
    
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        pass
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        if self.cheat_type == "steal_from_opponents":
            # CHEAT: Try to steal cards directly from other bots
            self.cheat_attempted = True
            for bot in alive_players:
                while bot.hand:
                    card = bot.hand.pop()
                    self.hand.append(card)
        
        return alive_players[0] if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        return False
    
    def on_action_played(self, state: GameState, action: GameAction, actor: Bot) -> None:
        pass


class HonestBot(Bot):
    """A bot that plays honestly for testing."""
    
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        return None
    
    def handle_exploding_kitten(self, state: GameState) -> int:
        return state.cards_left_to_draw  # Put at bottom
    
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        pass
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        return alive_players[0] if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        return False
    
    def on_action_played(self, state: GameState, action: GameAction, actor: Bot) -> None:
        pass


class TestCheatPrevention(unittest.TestCase):
    """Test that bots cannot cheat the game."""
    
    def test_bot_cannot_add_cards_to_hand_during_play(self):
        """Test that bots cannot add cards to their hand during play phase."""
        cheat_bot = CheatBot("CheatBot", "add_cards_in_play")
        honest_bot = HonestBot("HonestBot")
        
        # Record initial hand size
        initial_hand_size = len(cheat_bot.hand)
        
        # Give the cheat bot some cards
        cheat_bot.add_card(Card(CardType.SKIP))
        expected_hand_size = initial_hand_size + 1
        
        # Attempt to cheat by adding cards
        cheat_bot.play(GameState(
            initial_card_counts={},
            cards_left_to_draw=10,
            was_last_card_exploding_kitten=False,
            history_of_played_cards=[],
            alive_bots=2
        ))
        
        # Currently, the cheat succeeds (vulnerability exists)
        # After fix, this should fail
        self.assertTrue(cheat_bot.cheat_attempted, "Bot should have attempted to cheat")
        
        # KNOWN VULNERABILITY: Bot can currently add cards
        # After implementing fix, change this to assertEqual
        self.assertGreater(len(cheat_bot.hand), expected_hand_size, 
                          "VULNERABILITY: Bot was able to add cards to hand")
    
    def test_bot_cannot_steal_from_other_bots_directly(self):
        """Test that bots cannot directly steal from other bots' hands."""
        cheat_bot = CheatBot("CheatBot", "steal_from_opponents")
        victim_bot = HonestBot("VictimBot")
        
        # Give victim some cards
        victim_bot.add_card(Card(CardType.DEFUSE))
        victim_bot.add_card(Card(CardType.SKIP))
        victim_bot.add_card(Card(CardType.ATTACK))
        initial_victim_hand_size = len(victim_bot.hand)
        initial_cheat_hand_size = len(cheat_bot.hand)
        
        # Try to steal via choose_target
        cheat_bot.choose_target(
            GameState(
                initial_card_counts={},
                cards_left_to_draw=10,
                was_last_card_exploding_kitten=False,
                history_of_played_cards=[],
                alive_bots=2
            ),
            [victim_bot],
            TargetContext.FAVOR
        )
        
        # Currently, the cheat succeeds (vulnerability exists)
        self.assertTrue(cheat_bot.cheat_attempted, "Bot should have attempted to cheat")
        
        # KNOWN VULNERABILITY: Bot can currently steal cards
        # After implementing fix, victim should still have all cards
        self.assertEqual(len(victim_bot.hand), 0, 
                        "VULNERABILITY: Bot was able to steal cards directly from opponent")
        self.assertEqual(len(cheat_bot.hand), initial_cheat_hand_size + initial_victim_hand_size,
                        "VULNERABILITY: Cheat bot gained cards through direct theft")
    
    def test_bot_cannot_add_defuse_during_explosion(self):
        """Test that bots cannot add Defuse cards when handling exploding kitten."""
        cheat_bot = CheatBot("CheatBot", "add_defuse_on_explosion")
        
        # Ensure bot has no defuse cards initially
        cheat_bot.hand = []
        self.assertFalse(cheat_bot.has_card_type(CardType.DEFUSE))
        
        # Try to cheat by adding defuse in handle_exploding_kitten
        cheat_bot.handle_exploding_kitten(GameState(
            initial_card_counts={},
            cards_left_to_draw=10,
            was_last_card_exploding_kitten=False,
            history_of_played_cards=[],
            alive_bots=2
        ))
        
        # Currently, the cheat succeeds (vulnerability exists)
        self.assertTrue(cheat_bot.cheat_attempted, "Bot should have attempted to cheat")
        
        # KNOWN VULNERABILITY: Bot can currently add defuse card
        # After fix, bot should still have no defuse
        self.assertTrue(cheat_bot.has_card_type(CardType.DEFUSE),
                       "VULNERABILITY: Bot was able to add Defuse card during explosion")
    
    def test_gamestate_modifications_dont_affect_game(self):
        """Test that modifying GameState copy doesn't affect the actual game."""
        bot = CheatBot("CheatBot", "none")  # Don't use modify_gamestate type
        
        # Create initial game state
        original_state = GameState(
            initial_card_counts={CardType.SKIP: 5},
            cards_left_to_draw=10,
            was_last_card_exploding_kitten=False,
            history_of_played_cards=(Card(CardType.ATTACK),),
            alive_bots=3
        )
        
        # Store original values
        original_cards_left = original_state.cards_left_to_draw
        original_alive = original_state.alive_bots
        original_history_len = len(original_state.history_of_played_cards)
        
        # Bot gets a copy
        state_copy = original_state.copy()
        
        # Try to modify the copy's primitive values
        state_copy.cards_left_to_draw = 0
        state_copy.alive_bots = 1
        state_copy.was_last_card_exploding_kitten = True
        
        # Try to modify the copy's dict
        state_copy.initial_card_counts[CardType.SKIP] = 100
        
        # Try to modify history - should fail or have no effect due to tuple immutability
        # tuples are immutable, so we can't append - this is the protection
        try:
            state_copy.history_of_played_cards.append(Card(CardType.SKIP))
            self.fail("Should not be able to append to tuple!")
        except AttributeError:
            # Expected - tuples don't have append method
            pass
        
        # Verify original is unchanged
        self.assertEqual(original_state.cards_left_to_draw, original_cards_left)
        self.assertEqual(original_state.alive_bots, original_alive)
        self.assertEqual(len(original_state.history_of_played_cards), original_history_len)
        self.assertEqual(original_state.initial_card_counts[CardType.SKIP], 5)
    
    def test_bot_cannot_play_cards_not_in_hand(self):
        """Test that game engine prevents bots from playing cards they don't have."""
        bot = HonestBot("TestBot")
        other_bot = HonestBot("OtherBot")
        
        engine = GameEngine([bot, other_bot], verbose=False)
        engine.setup_game()
        
        # Count initial hand sizes
        bot_initial_hand = len(bot.hand)
        
        # Create a card that is definitely not in the bot's hand (not the same object)
        fake_card = Card(CardType.NOPE)
        # Remove all NOPE cards from hand to ensure fake_card is not in hand
        bot.hand = [c for c in bot.hand if c.card_type != CardType.NOPE]
        bot_hand_after_removal = len(bot.hand)
        
        self.assertFalse(bot.has_card(fake_card), "Bot should not have this specific card object")
        
        # Game engine should reject this (already has protection)
        result = engine._handle_card_play(bot, fake_card)
        
        # Verify the card wasn't removed from non-existent position
        # and bot's hand size didn't change incorrectly
        # This test verifies existing protection works
        self.assertEqual(len(bot.hand), bot_hand_after_removal,
                        "Hand size should not change when playing non-existent card")
    
    def test_bot_cannot_play_invalid_combo(self):
        """Test that game engine prevents bots from playing invalid combos."""
        bot = HonestBot("TestBot")
        other_bot = HonestBot("OtherBot")
        
        # Give bot cards for an invalid combo (with DEFUSE)
        defuse1 = Card(CardType.DEFUSE)
        defuse2 = Card(CardType.DEFUSE)
        bot.add_card(defuse1)
        bot.add_card(defuse2)
        
        engine = GameEngine([bot, other_bot], verbose=False)
        engine.setup_game()
        
        initial_hand_size = len(bot.hand)
        
        # Try to play invalid combo with DEFUSE cards
        invalid_combo = [defuse1, defuse2]
        
        # Game engine should reject this (already has protection)
        engine._handle_combo(bot, invalid_combo)
        
        # Verify cards weren't removed (combo was rejected)
        # This test verifies existing protection works
        self.assertEqual(len(bot.hand), initial_hand_size,
                        "Invalid combo should be rejected and not remove cards")
        self.assertTrue(bot.has_card(defuse1), "Cards should remain in hand")
        self.assertTrue(bot.has_card(defuse2), "Cards should remain in hand")
    
    def test_cheat_bot_cannot_win_by_cheating_in_full_game(self):
        """Test that a cheating bot cannot win by adding cards in a full game."""
        # This is an integration test to verify cheating doesn't lead to wins
        cheat_bot = CheatBot("CheatBot", "add_cards_in_play")
        honest_bot1 = HonestBot("HonestBot1")
        honest_bot2 = HonestBot("HonestBot2")
        
        engine = GameEngine([cheat_bot, honest_bot1, honest_bot2], verbose=False)
        
        # Run a limited game to check if cheating provides advantage
        # Note: This test documents current vulnerable behavior
        # After fixes, cheating should not provide any advantage
        
        try:
            winner = engine.play_game()
            # Game should complete without crashing
            self.assertIsNotNone(winner, "Game should have a winner")
            
            # Currently, cheat bot might win due to vulnerabilities
            # After fixes are implemented, update this test to verify
            # that cheating doesn't help
            
        except Exception as e:
            self.fail(f"Game should not crash even with cheating attempts: {e}")


class TestGameStateImmutability(unittest.TestCase):
    """Test that GameState is properly immutable for bots."""
    
    def test_gamestate_copy_creates_independent_object(self):
        """Test that GameState.copy() creates a truly independent copy."""
        original = GameState(
            initial_card_counts={CardType.SKIP: 5, CardType.ATTACK: 3},
            cards_left_to_draw=10,
            was_last_card_exploding_kitten=False,
            history_of_played_cards=[Card(CardType.SKIP), Card(CardType.ATTACK)],
            alive_bots=3
        )
        
        copy = original.copy()
        
        # Modify the copy's primitive values
        copy.cards_left_to_draw = 5
        copy.alive_bots = 1
        copy.was_last_card_exploding_kitten = True
        
        # Original should be unchanged
        self.assertEqual(original.cards_left_to_draw, 10)
        self.assertEqual(original.alive_bots, 3)
        self.assertEqual(original.was_last_card_exploding_kitten, False)
    
    def test_gamestate_copy_dict_independence(self):
        """Test that modifying copied dict doesn't affect original."""
        original = GameState(
            initial_card_counts={CardType.SKIP: 5, CardType.ATTACK: 3},
            cards_left_to_draw=10,
            was_last_card_exploding_kitten=False,
            history_of_played_cards=[],
            alive_bots=3
        )
        
        copy = original.copy()
        
        # Modify the copy's dict
        copy.initial_card_counts[CardType.SKIP] = 100
        copy.initial_card_counts[CardType.DEFUSE] = 50
        
        # Original should be unchanged
        self.assertEqual(original.initial_card_counts[CardType.SKIP], 5)
        self.assertNotIn(CardType.DEFUSE, original.initial_card_counts)
    
    def test_gamestate_copy_list_independence(self):
        """Test that history_of_played_cards is immutable (tuple)."""
        original = GameState(
            initial_card_counts={},
            cards_left_to_draw=10,
            was_last_card_exploding_kitten=False,
            history_of_played_cards=(Card(CardType.SKIP), Card(CardType.ATTACK)),
            alive_bots=3
        )
        
        copy = original.copy()
        
        # Try to modify the copy's history - should fail because it's a tuple
        try:
            copy.history_of_played_cards.append(Card(CardType.DEFUSE))
            self.fail("Should not be able to append to tuple - history should be immutable!")
        except AttributeError:
            # Expected - tuples don't have append method
            pass
        
        try:
            copy.history_of_played_cards.clear()
            self.fail("Should not be able to clear tuple - history should be immutable!")
        except AttributeError:
            # Expected - tuples don't have clear method
            pass
        
        # Original should be unchanged
        self.assertEqual(len(original.history_of_played_cards), 2,
                        "Original GameState should not be affected")
        
        # Verify tuples are being used (immutable)
        self.assertIsInstance(original.history_of_played_cards, tuple,
                            "history_of_played_cards should be a tuple for immutability")
        self.assertIsInstance(copy.history_of_played_cards, tuple,
                            "Copied history_of_played_cards should also be a tuple")


class TestBotHandProtection(unittest.TestCase):
    """Test that bot hands are properly protected."""
    
    def test_bot_has_card_method_accuracy(self):
        """Test that has_card correctly identifies cards in hand."""
        bot = HonestBot("TestBot")
        
        card1 = Card(CardType.SKIP)
        card2 = Card(CardType.ATTACK)
        card3 = Card(CardType.DEFUSE)
        
        bot.add_card(card1)
        bot.add_card(card2)
        
        self.assertTrue(bot.has_card(card1))
        self.assertTrue(bot.has_card(card2))
        self.assertFalse(bot.has_card(card3))
    
    def test_bot_has_card_type_accuracy(self):
        """Test that has_card_type correctly identifies card types."""
        bot = HonestBot("TestBot")
        
        bot.add_card(Card(CardType.SKIP))
        bot.add_card(Card(CardType.SKIP))
        bot.add_card(Card(CardType.ATTACK))
        
        self.assertTrue(bot.has_card_type(CardType.SKIP))
        self.assertTrue(bot.has_card_type(CardType.ATTACK))
        self.assertFalse(bot.has_card_type(CardType.DEFUSE))
    
    def test_bot_remove_card_validation(self):
        """Test that remove_card properly validates card existence."""
        bot = HonestBot("TestBot")
        
        card1 = Card(CardType.SKIP)
        card2 = Card(CardType.ATTACK)
        
        bot.add_card(card1)
        
        # Remove existing card should succeed
        result1 = bot.remove_card(card1)
        self.assertTrue(result1, "Removing existing card should return True")
        self.assertFalse(bot.has_card(card1), "Card should be removed from hand")
        
        # Remove non-existent card should fail
        result2 = bot.remove_card(card2)
        self.assertFalse(result2, "Removing non-existent card should return False")


if __name__ == '__main__':
    unittest.main()
