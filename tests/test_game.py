"""Tests for the Exploding Kittens game components."""

import unittest
from game import Card, CardType, ComboType, TargetContext, GameState, Bot, Deck, GameEngine
from typing import Optional, List, Union, Dict


class SimpleBot(Bot):
    """A simple test bot for testing purposes."""
    
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        return None
    
    def handle_exploding_kitten(self, state: GameState) -> int:
        return 0
    
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        pass
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: str) -> Optional[Bot]:
        return alive_players[0] if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action_description: str) -> bool:
        return False


class TestCard(unittest.TestCase):
    """Test Card class."""
    
    def test_card_creation(self):
        """Test creating cards of different types."""
        card = Card(CardType.DEFUSE)
        self.assertEqual(card.card_type, CardType.DEFUSE)
        
    def test_card_str(self):
        """Test string representation of cards."""
        card = Card(CardType.EXPLODING_KITTEN)
        self.assertEqual(str(card), "Exploding Kitten")


class TestDeck(unittest.TestCase):
    """Test Deck class."""
    
    def test_deck_initialization(self):
        """Test deck is initialized with correct number of cards."""
        deck = Deck(3)
        initial_size = deck.size()
        # Deck starts with cards but no Exploding Kittens yet
        self.assertGreater(initial_size, 0)
    
    def test_draw_card(self):
        """Test drawing cards from deck."""
        deck = Deck(2)
        initial_size = deck.size()
        card = deck.draw()
        self.assertIsInstance(card, Card)
        self.assertEqual(deck.size(), initial_size - 1)
    
    def test_insert_at(self):
        """Test inserting cards at specific positions."""
        deck = Deck(2)
        initial_size = deck.size()
        new_card = Card(CardType.SKIP)
        deck.insert_at(new_card, 0)
        self.assertEqual(deck.size(), initial_size + 1)
        drawn = deck.draw()
        self.assertEqual(drawn.card_type, CardType.SKIP)
    
    def test_peek(self):
        """Test peeking at cards without removing them."""
        deck = Deck(2)
        initial_size = deck.size()
        peeked = deck.peek(3)
        self.assertEqual(deck.size(), initial_size)
        self.assertLessEqual(len(peeked), 3)
    
    def test_shuffle(self):
        """Test deck shuffling."""
        deck = Deck(2)
        # Just ensure shuffle doesn't crash
        deck.shuffle()
        self.assertGreater(deck.size(), 0)


class TestBotClass(unittest.TestCase):
    """Test Bot class."""
    
    def test_bot_initialization(self):
        """Test bot initialization."""
        bot = SimpleBot("TestBot")
        self.assertEqual(bot.name, "TestBot")
        self.assertEqual(len(bot.hand), 0)
        self.assertTrue(bot.alive)
    
    def test_add_remove_card(self):
        """Test adding and removing cards from bot's hand."""
        bot = SimpleBot("TestBot")
        card = Card(CardType.DEFUSE)
        bot.add_card(card)
        self.assertEqual(len(bot.hand), 1)
        self.assertTrue(bot.has_card(card))
        
        bot.remove_card(card)
        self.assertEqual(len(bot.hand), 0)
        self.assertFalse(bot.has_card(card))
    
    def test_has_card_type(self):
        """Test checking for card types."""
        bot = SimpleBot("TestBot")
        bot.add_card(Card(CardType.DEFUSE))
        self.assertTrue(bot.has_card_type(CardType.DEFUSE))
        self.assertFalse(bot.has_card_type(CardType.SKIP))


class TestGameState(unittest.TestCase):
    """Test GameState class."""
    
    def test_game_state_creation(self):
        """Test creating a game state."""
        initial_counts = {
            CardType.EXPLODING_KITTEN: 2,
            CardType.DEFUSE: 4,
            CardType.SKIP: 3
        }
        state = GameState(
            initial_card_counts=initial_counts,
            cards_left_to_draw=10,
            was_last_card_exploding_kitten=False,
            alive_bots=3
        )
        self.assertEqual(state.cards_left_to_draw, 10)
        self.assertEqual(state.alive_bots, 3)
        self.assertFalse(state.was_last_card_exploding_kitten)
        self.assertEqual(state.initial_card_counts[CardType.EXPLODING_KITTEN], 2)
    
    def test_game_state_copy(self):
        """Test copying game state."""
        state = GameState(
            initial_card_counts={CardType.DEFUSE: 6, CardType.SKIP: 4},
            cards_left_to_draw=5,
            was_last_card_exploding_kitten=True,
            alive_bots=2
        )
        copy = state.copy()
        self.assertEqual(copy.cards_left_to_draw, state.cards_left_to_draw)
        self.assertEqual(copy.alive_bots, state.alive_bots)
        self.assertEqual(copy.initial_card_counts, state.initial_card_counts)


class NopeBot(Bot):
    """Bot that always plays Nope when possible."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.will_nope = True
    
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        return None
    
    def handle_exploding_kitten(self, state: GameState) -> int:
        return 0
    
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
    
    def should_play_nope(self, state: GameState, action_description: str) -> bool:
        return self.will_nope


class ComboBot(Bot):
    """Bot that plays combos when instructed."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.combo_to_play = None
    
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        if self.combo_to_play:
            combo = self.combo_to_play
            self.combo_to_play = None
            return combo
        return None
    
    def handle_exploding_kitten(self, state: GameState) -> int:
        return 0
    
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        pass
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        return alive_players[0] if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        # Give away first non-Defuse card
        for card in self.hand:
            if card.card_type != CardType.DEFUSE:
                return card
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        return CardType.SKIP
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action_description: str) -> bool:
        return False


class TestCombos(unittest.TestCase):
    """Test combo mechanics."""
    
    def test_valid_2_of_a_kind(self):
        """Test that 2-of-a-kind combo is recognized."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        cards = [Card(CardType.SKIP), Card(CardType.SKIP)]
        combo_type = game._is_valid_combo(cards)
        self.assertEqual(combo_type, ComboType.TWO_OF_A_KIND)
    
    def test_valid_3_of_a_kind(self):
        """Test that 3-of-a-kind combo is recognized."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        cards = [Card(CardType.ATTACK), Card(CardType.ATTACK), Card(CardType.ATTACK)]
        combo_type = game._is_valid_combo(cards)
        self.assertEqual(combo_type, ComboType.THREE_OF_A_KIND)
    
    def test_valid_5_unique(self):
        """Test that 5-unique combo is recognized."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        cards = [
            Card(CardType.SKIP),
            Card(CardType.ATTACK),
            Card(CardType.SHUFFLE),
            Card(CardType.TACOCAT),
            Card(CardType.FAVOR)  # Changed from DEFUSE
        ]
        combo_type = game._is_valid_combo(cards)
        self.assertEqual(combo_type, ComboType.FIVE_UNIQUE)
    
    def test_invalid_combo_wrong_count(self):
        """Test that invalid card counts are rejected."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        cards = [Card(CardType.SKIP)]
        combo_type = game._is_valid_combo(cards)
        self.assertIsNone(combo_type)
    
    def test_invalid_2_of_a_kind_different_types(self):
        """Test that 2 different cards are not a valid combo."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        cards = [Card(CardType.SKIP), Card(CardType.ATTACK)]
        combo_type = game._is_valid_combo(cards)
        self.assertIsNone(combo_type)
    
    def test_invalid_5_unique_duplicates(self):
        """Test that 5 cards with duplicates is not valid."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        cards = [
            Card(CardType.SKIP),
            Card(CardType.SKIP),
            Card(CardType.ATTACK),
            Card(CardType.SHUFFLE),
            Card(CardType.DEFUSE)
        ]
        combo_type = game._is_valid_combo(cards)
        self.assertIsNone(combo_type)
    
    def test_invalid_combo_with_exploding_kitten(self):
        """Test that Exploding Kitten cards cannot be used in combos."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        # Try 2-of-a-kind with Exploding Kittens
        cards = [Card(CardType.EXPLODING_KITTEN), Card(CardType.EXPLODING_KITTEN)]
        combo_type = game._is_valid_combo(cards)
        self.assertIsNone(combo_type)
    
    def test_invalid_combo_with_defuse(self):
        """Test that Defuse cards cannot be used in combos."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        # Try 2-of-a-kind with Defuse cards
        cards = [Card(CardType.DEFUSE), Card(CardType.DEFUSE)]
        combo_type = game._is_valid_combo(cards)
        self.assertIsNone(combo_type)
    
    def test_invalid_5_unique_with_defuse(self):
        """Test that 5-unique with Defuse is invalid."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        cards = [
            Card(CardType.SKIP),
            Card(CardType.ATTACK),
            Card(CardType.SHUFFLE),
            Card(CardType.TACOCAT),
            Card(CardType.DEFUSE)  # Defuse not allowed
        ]
        combo_type = game._is_valid_combo(cards)
        self.assertIsNone(combo_type)
    
    def test_2_of_a_kind_steals_card(self):
        """Test that 2-of-a-kind combo steals a random card."""
        bot1 = ComboBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Give bot1 a 2-of-a-kind combo
        bot1.hand = [Card(CardType.TACOCAT), Card(CardType.TACOCAT)]
        bot2.hand = [Card(CardType.SKIP)]
        
        # Execute combo
        bot1.combo_to_play = bot1.hand.copy()
        game.setup_game = lambda: None  # Skip setup
        game.bots = [bot1, bot2]
        game._handle_combo(bot1, bot1.hand.copy())
        
        # Bot1 should have stolen the card
        self.assertEqual(len(bot1.hand), 1)
        self.assertEqual(len(bot2.hand), 0)
    
    def test_3_of_a_kind_requests_specific_card(self):
        """Test that 3-of-a-kind combo can request specific card."""
        bot1 = ComboBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Give bot1 a 3-of-a-kind combo
        bot1.hand = [Card(CardType.TACOCAT), Card(CardType.TACOCAT), Card(CardType.TACOCAT)]
        bot2.hand = [Card(CardType.SKIP), Card(CardType.ATTACK)]
        
        # Execute combo
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game._handle_combo(bot1, bot1.hand.copy())
        
        # Bot1 should have requested and received a card
        self.assertEqual(len(bot1.hand), 1)  # Lost 3, gained 1
        self.assertEqual(len(bot2.hand), 1)  # Lost 1
    
    def test_5_unique_takes_from_discard(self):
        """Test that 5-unique combo takes card from discard."""
        bot1 = ComboBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Give bot1 5 unique cards
        bot1.hand = [
            Card(CardType.TACOCAT),
            Card(CardType.SKIP),
            Card(CardType.ATTACK),
            Card(CardType.SHUFFLE),
            Card(CardType.SEE_THE_FUTURE)
        ]
        game.deck.discard_pile = [Card(CardType.DEFUSE)]
        
        # Execute combo
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game._handle_combo(bot1, bot1.hand.copy())
        
        # Bot1 should have taken from discard
        self.assertEqual(len(bot1.hand), 1)  # Lost 5, gained 1
        self.assertEqual(len(game.deck.discard_pile), 5)  # 5 from combo


class TestNopeCard(unittest.TestCase):
    """Test Nope card mechanics."""
    
    def test_single_nope_cancels_action(self):
        """Test that a single Nope cancels an action."""
        bot1 = SimpleBot("Bot1")
        bot2 = NopeBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Give bot2 a Nope card
        bot2.hand = [Card(CardType.NOPE)]
        
        # Check if action gets noped
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        was_noped = game._check_for_nope("Bot1 playing Skip", bot1)
        
        self.assertTrue(was_noped)
        self.assertEqual(len(bot2.hand), 0)  # Nope was used
    
    def test_double_nope_allows_action(self):
        """Test that two Nopes allow the action (nope the nope)."""
        bot1 = SimpleBot("Bot1")
        bot2 = NopeBot("Bot2")
        bot3 = NopeBot("Bot3")
        game = GameEngine([bot1, bot2, bot3], verbose=False)
        
        # Give both bots Nope cards
        bot2.hand = [Card(CardType.NOPE)]
        bot3.hand = [Card(CardType.NOPE)]
        
        game.setup_game = lambda: None
        game.bots = [bot1, bot2, bot3]
        was_noped = game._check_for_nope("Bot1 playing Skip", bot1)
        
        # Even number of nopes = action proceeds
        self.assertFalse(was_noped)
        self.assertEqual(len(bot2.hand), 0)
        self.assertEqual(len(bot3.hand), 0)
    
    def test_triple_nope_cancels_action(self):
        """Test that three Nopes cancel the action."""
        bot1 = NopeBot("Bot1")
        bot2 = NopeBot("Bot2")
        bot3 = NopeBot("Bot3")
        bot4 = SimpleBot("Bot4")
        game = GameEngine([bot4, bot1, bot2, bot3], verbose=False)
        
        # Give bots Nope cards
        bot1.hand = [Card(CardType.NOPE)]
        bot2.hand = [Card(CardType.NOPE)]
        bot3.hand = [Card(CardType.NOPE)]
        
        game.setup_game = lambda: None
        game.bots = [bot4, bot1, bot2, bot3]
        was_noped = game._check_for_nope("Bot4 playing Attack", bot4)
        
        # Odd number of nopes = action canceled
        self.assertTrue(was_noped)
    
    def test_nope_order_follows_play_order(self):
        """Test that bots are asked to nope in play order."""
        bot1 = SimpleBot("Bot1")
        bot2 = NopeBot("Bot2")
        bot3 = SimpleBot("Bot3")
        game = GameEngine([bot1, bot2, bot3], verbose=False)
        
        bot2.hand = [Card(CardType.NOPE)]
        bot2.will_nope = True
        
        game.setup_game = lambda: None
        game.bots = [bot1, bot2, bot3]
        
        # Bot1 plays action, bot2 should be asked first (next in order)
        was_noped = game._check_for_nope("Bot1 playing Attack", bot1)
        
        self.assertTrue(was_noped)
        self.assertEqual(len(bot2.hand), 0)
    
    def test_no_nope_without_nope_card(self):
        """Test that bots without Nope cards can't nope."""
        bot1 = SimpleBot("Bot1")
        bot2 = NopeBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Bot2 wants to nope but has no Nope card
        bot2.hand = [Card(CardType.SKIP)]
        bot2.will_nope = True
        
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        was_noped = game._check_for_nope("Bot1 playing Attack", bot1)
        
        self.assertFalse(was_noped)
    
    def test_dead_bots_cannot_nope(self):
        """Test that dead bots are not asked to nope."""
        bot1 = SimpleBot("Bot1")
        bot2 = NopeBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        bot2.hand = [Card(CardType.NOPE)]
        bot2.alive = False  # Bot is dead
        
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        was_noped = game._check_for_nope("Bot1 playing Attack", bot1)
        
        self.assertFalse(was_noped)
        self.assertEqual(len(bot2.hand), 1)  # Nope not used


class TestCatCards(unittest.TestCase):
    """Test the 5 different cat card types."""
    
    def test_all_cat_types_exist(self):
        """Test that all 5 cat types are defined."""
        cat_types = [
            CardType.TACOCAT,
            CardType.CATTERMELON,
            CardType.HAIRY_POTATO_CAT,
            CardType.BEARD_CAT,
            CardType.RAINBOW_RALPHING_CAT
        ]
        for cat_type in cat_types:
            card = Card(cat_type)
            self.assertIsNotNone(card)
    
    def test_deck_contains_cat_cards(self):
        """Test that deck is initialized with cat cards."""
        deck = Deck(3)
        cat_types = [
            CardType.TACOCAT,
            CardType.CATTERMELON,
            CardType.HAIRY_POTATO_CAT,
            CardType.BEARD_CAT,
            CardType.RAINBOW_RALPHING_CAT
        ]
        
        # Count cat cards in deck
        all_cards = deck.draw_pile + deck.discard_pile
        cat_counts = {ct: sum(1 for c in all_cards if c.card_type == ct) for ct in cat_types}
        
        # Each cat type should have 4 cards
        for cat_type, count in cat_counts.items():
            self.assertEqual(count, 4, f"{cat_type} should have 4 cards")
    
    def test_cat_cards_can_form_combos(self):
        """Test that cat cards can be used in combos."""
        game = GameEngine([SimpleBot("Bot1"), SimpleBot("Bot2")], verbose=False)
        
        # Test 2-of-a-kind with cat cards
        combo = [Card(CardType.TACOCAT), Card(CardType.TACOCAT)]
        self.assertEqual(game._is_valid_combo(combo), ComboType.TWO_OF_A_KIND)
        
        # Test 3-of-a-kind with cat cards
        combo = [Card(CardType.BEARD_CAT), Card(CardType.BEARD_CAT), Card(CardType.BEARD_CAT)]
        self.assertEqual(game._is_valid_combo(combo), ComboType.THREE_OF_A_KIND)


class TestFavorCard(unittest.TestCase):
    """Test Favor card mechanics."""
    
    def test_favor_asks_target_for_card(self):
        """Test that Favor card asks target to choose which card to give."""
        bot1 = SimpleBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        bot1.hand = []
        bot2.hand = [Card(CardType.SKIP), Card(CardType.ATTACK)]
        
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game._execute_favor(bot1)
        
        # Bot1 should have received a card from bot2
        self.assertEqual(len(bot1.hand), 1)
        self.assertEqual(len(bot2.hand), 1)
    
    def test_favor_no_target_available(self):
        """Test Favor when no targets are available."""
        bot1 = SimpleBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        bot2.alive = False  # No alive targets
        
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game._execute_favor(bot1)
        
        # Nothing should happen
        self.assertEqual(len(bot1.hand), 0)


class TestGameEngine(unittest.TestCase):
    """Test GameEngine class."""
    
    def test_game_requires_minimum_players(self):
        """Test that game requires at least 2 players."""
        bot1 = SimpleBot("Bot1")
        with self.assertRaises(ValueError):
            GameEngine([bot1], verbose=False)
    
    def test_game_with_two_players(self):
        """Test a game with two players completes."""
        bot1 = SimpleBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        winner = game.play_game()
        self.assertIsNotNone(winner)
        self.assertIn(winner, [bot1, bot2])
    
    def test_game_setup(self):
        """Test game setup."""
        bot1 = SimpleBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        game.setup_game()
        
        # Each bot should have 7 cards
        self.assertEqual(len(bot1.hand), 7)
        self.assertEqual(len(bot2.hand), 7)
        
        # Each bot should have at least one Defuse
        self.assertTrue(bot1.has_card_type(CardType.DEFUSE))
        self.assertTrue(bot2.has_card_type(CardType.DEFUSE))
        
        # Game state should be initialized
        self.assertGreater(game.game_state.cards_left_to_draw, 0)
        self.assertEqual(game.game_state.alive_bots, 2)


class TestMultiTurnMechanics(unittest.TestCase):
    """Test multi-turn mechanics with Attack and Skip cards."""
    
    def test_single_attack_gives_2_turns(self):
        """Test that Attack card gives next player 2 turns."""
        bot1 = SimpleBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup game state
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game.turns_to_take = 1
        game.current_bot_index = 0
        
        # Bot1 plays Attack
        bot1.hand = [Card(CardType.ATTACK)]
        game._handle_card_play(bot1, Card(CardType.ATTACK))
        
        # turns_to_take should be -2 (negative signals Attack)
        self.assertEqual(game.turns_to_take, -2)
    
    def test_double_attack_stacks(self):
        """Test that Attack → Attack gives next player 3 turns."""
        bot1 = SimpleBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game.turns_to_take = 2  # Bot has 2 turns from previous Attack
        
        # Bot plays Attack while having 2 turns
        bot1.hand = [Card(CardType.ATTACK)]
        game._handle_card_play(bot1, Card(CardType.ATTACK))
        
        # Should be -(2 + 1) = -3
        self.assertEqual(game.turns_to_take, -3)
    
    def test_triple_attack_stacks(self):
        """Test that Attack → Attack → Attack gives 4 turns."""
        bot1 = SimpleBot("Bot1")
        game = GameEngine([bot1, SimpleBot("Bot2")], verbose=False)
        
        game.setup_game = lambda: None
        game.turns_to_take = 3  # Has 3 turns
        
        bot1.hand = [Card(CardType.ATTACK)]
        game._handle_card_play(bot1, Card(CardType.ATTACK))
        
        # Should be -(3 + 1) = -4
        self.assertEqual(game.turns_to_take, -4)
    
    def test_skip_with_multiple_turns(self):
        """Test that Skip only ends one turn when bot has multiple turns."""
        bot1 = SimpleBot("Bot1")
        game = GameEngine([bot1, SimpleBot("Bot2")], verbose=False)
        
        game.setup_game = lambda: None
        game.turns_to_take = 3
        
        bot1.hand = [Card(CardType.SKIP)]
        game._handle_card_play(bot1, Card(CardType.SKIP))
        
        # Skip doesn't modify turns_to_take directly anymore
        # It's handled in the play phase
        # Just verify the card effect doesn't set it to 0
        self.assertEqual(game.turns_to_take, 3)
    
    def test_bot_with_no_cards_can_only_draw(self):
        """Test that bot with empty hand can still draw and be notified."""
        bot1 = SimpleBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup minimal game state
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game.deck.draw_pile = [Card(CardType.SKIP), Card(CardType.ATTACK)]
        game.game_state.cards_left_to_draw = 2
        
        # Bot1 has no cards
        bot1.hand = []
        bot1.alive = True
        
        # Bot should still be able to draw
        game._draw_phase(bot1)
        
        # Bot should now have 1 card
        self.assertEqual(len(bot1.hand), 1)
    
    def test_bot_with_no_cards_receives_notifications(self):
        """Test that bot with no cards still gets Nope notifications."""
        bot1 = SimpleBot("Bot1")
        bot2 = NopeBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Bot2 has only Nope card
        bot2.hand = [Card(CardType.NOPE)]
        bot2.will_nope = True
        
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        
        # Bot1 plays action (bot1 has no cards but that's ok for this test)
        was_noped = game._check_for_nope("Bot1 playing Attack", bot1)
        
        # Bot2 should have been able to Nope
        self.assertTrue(was_noped)
        self.assertEqual(len(bot2.hand), 0)


class TestDeckConfiguration(unittest.TestCase):
    """Test deck configuration system."""
    
    def test_default_deck_config(self):
        """Test that default deck configuration works."""
        deck = Deck(3)
        initial_counts = deck.get_initial_card_counts()
        
        # Check some expected counts
        self.assertEqual(initial_counts[CardType.DEFUSE], 6)
        self.assertEqual(initial_counts[CardType.SKIP], 4)
        self.assertEqual(initial_counts[CardType.EXPLODING_KITTEN], 2)  # 3 players - 1
        self.assertEqual(initial_counts[CardType.TACOCAT], 4)
    
    def test_custom_deck_config(self):
        """Test that custom deck configuration works."""
        custom_config = {
            CardType.DEFUSE: 10,
            CardType.SKIP: 8,
            CardType.ATTACK: 2,
        }
        deck = Deck(2, custom_config)
        initial_counts = deck.get_initial_card_counts()
        
        # Custom values should override defaults
        self.assertEqual(initial_counts[CardType.DEFUSE], 10)
        self.assertEqual(initial_counts[CardType.SKIP], 8)
        self.assertEqual(initial_counts[CardType.ATTACK], 2)
        
        # Non-overridden values should use defaults
        self.assertEqual(initial_counts[CardType.NOPE], 5)
        
        # Exploding Kittens based on players
        self.assertEqual(initial_counts[CardType.EXPLODING_KITTEN], 1)  # 2 players - 1
    
    def test_game_engine_with_custom_config(self):
        """Test GameEngine with custom deck config."""
        custom_config = {
            CardType.DEFUSE: 12,
            CardType.NOPE: 10,
        }
        bot1 = SimpleBot("Bot1")
        bot2 = SimpleBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False, deck_config=custom_config)
        game.setup_game()
        
        # Check that game state has the custom initial counts
        self.assertEqual(game.game_state.initial_card_counts[CardType.DEFUSE], 12)
        self.assertEqual(game.game_state.initial_card_counts[CardType.NOPE], 10)


class TrackingBot(Bot):
    """A bot that tracks all notifications for testing."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.notifications = []
    
    def on_action_played(self, state: GameState, action_description: str, actor: 'Bot') -> None:
        """Track all notifications."""
        self.notifications.append({
            'action': action_description,
            'actor': actor.name,
            'cards_left': state.cards_left_to_draw
        })
    
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        return None
    
    def handle_exploding_kitten(self, state: GameState) -> int:
        return 0
    
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        pass
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        return alive_players[0] if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        return CardType.SKIP
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action_description: str) -> bool:
        return False


class TestNotificationSystem(unittest.TestCase):
    """Test bot notification system."""
    
    def test_bots_notified_about_card_plays(self):
        """Test that all bots are notified when a card is played."""
        bot1 = TrackingBot("Bot1")
        bot2 = TrackingBot("Bot2")
        bot3 = TrackingBot("Bot3")
        game = GameEngine([bot1, bot2, bot3], verbose=False)
        
        # Setup
        game.setup_game = lambda: None
        game.bots = [bot1, bot2, bot3]
        bot1.hand = [Card(CardType.SKIP)]
        
        # Bot1 plays Skip
        game._handle_card_play(bot1, Card(CardType.SKIP))
        
        # All bots should be notified (including bot1)
        self.assertEqual(len(bot1.notifications), 1)
        self.assertEqual(len(bot2.notifications), 1)
        self.assertEqual(len(bot3.notifications), 1)
        
        # Check notification content
        self.assertIn("Bot1 playing Skip", bot1.notifications[0]['action'])
        self.assertEqual(bot1.notifications[0]['actor'], 'Bot1')
    
    def test_bots_notified_about_draws(self):
        """Test that all bots are notified when a card is drawn."""
        bot1 = TrackingBot("Bot1")
        bot2 = TrackingBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game.deck.draw_pile = [Card(CardType.SKIP)]
        game.game_state.cards_left_to_draw = 1
        bot1.alive = True
        bot2.alive = True
        
        # Bot1 draws
        game._draw_phase(bot1)
        
        # Both bots should be notified
        self.assertEqual(len(bot1.notifications), 1)
        self.assertEqual(len(bot2.notifications), 1)
        self.assertIn("draws a card", bot1.notifications[0]['action'])
    
    def test_bots_notified_about_exploding_kitten(self):
        """Test that bots are notified when someone draws Exploding Kitten."""
        bot1 = TrackingBot("Bot1")
        bot2 = TrackingBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game.deck.draw_pile = [Card(CardType.EXPLODING_KITTEN)]
        game.game_state.cards_left_to_draw = 1
        bot1.hand = [Card(CardType.DEFUSE)]
        bot1.alive = True
        bot2.alive = True
        
        # Bot1 draws Exploding Kitten
        game._draw_phase(bot1)
        
        # Both bots should be notified about both the draw and the defuse
        self.assertGreaterEqual(len(bot1.notifications), 2)
        self.assertGreaterEqual(len(bot2.notifications), 2)
        
        # Check for Exploding Kitten notification
        actions = [n['action'] for n in bot1.notifications]
        self.assertTrue(any("Exploding Kitten" in action for action in actions))
        self.assertTrue(any("defused" in action for action in actions))
    
    def test_bots_notified_about_elimination(self):
        """Test that bots are notified when a bot explodes."""
        bot1 = TrackingBot("Bot1")
        bot2 = TrackingBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        game.deck.draw_pile = [Card(CardType.EXPLODING_KITTEN)]
        game.game_state.cards_left_to_draw = 1
        bot1.hand = []  # No Defuse
        bot1.alive = True
        bot2.alive = True
        
        # Bot1 draws Exploding Kitten and explodes
        game._draw_phase(bot1)
        
        # Bot2 should be notified about elimination
        actions = [n['action'] for n in bot2.notifications]
        self.assertTrue(any("eliminated" in action or "exploded" in action for action in actions))
    
    def test_actor_notified_about_own_actions(self):
        """Test that the actor is notified about their own actions."""
        bot1 = TrackingBot("Bot1")
        bot2 = TrackingBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        bot1.hand = [Card(CardType.SHUFFLE)]
        
        # Bot1 plays Shuffle
        game._handle_card_play(bot1, Card(CardType.SHUFFLE))
        
        # Bot1 should be notified about their own action
        self.assertEqual(len(bot1.notifications), 1)
        self.assertEqual(bot1.notifications[0]['actor'], 'Bot1')
        self.assertIn("Shuffle", bot1.notifications[0]['action'])
    
    def test_notification_order_with_nope(self):
        """Test that notifications happen before Nope checks."""
        bot1 = TrackingBot("Bot1")
        bot2 = TrackingBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        bot1.hand = [Card(CardType.ATTACK)]
        bot2.hand = []  # No Nope
        bot1.alive = True
        bot2.alive = True
        
        # Clear notifications
        bot1.notifications = []
        bot2.notifications = []
        
        # Bot1 plays Attack
        game._handle_card_play(bot1, Card(CardType.ATTACK))
        
        # Both should be notified even though neither has Nope
        self.assertGreaterEqual(len(bot1.notifications), 1)
        self.assertGreaterEqual(len(bot2.notifications), 1)
    
    def test_bots_notified_about_combo_results(self):
        """Test that bots are notified about combo results."""
        bot1 = TrackingBot("Bot1")
        bot2 = TrackingBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        bot1.hand = []
        bot2.hand = [Card(CardType.SKIP)]
        bot1.alive = True
        bot2.alive = True
        
        # Clear notifications
        bot1.notifications = []
        bot2.notifications = []
        
        # Execute 2-of-a-kind (bot1 steals from bot2)
        game._execute_2_of_a_kind_with_target(bot1, bot2)
        
        # Both should be notified about the steal
        self.assertGreaterEqual(len(bot1.notifications), 1)
        self.assertGreaterEqual(len(bot2.notifications), 1)
        
        # Check notification content
        actions = [n['action'] for n in bot1.notifications]
        self.assertTrue(any("steals" in action for action in actions))
    
    def test_bots_notified_about_favor_result(self):
        """Test that bots are notified about Favor card results."""
        bot1 = TrackingBot("Bot1")
        bot2 = TrackingBot("Bot2")
        game = GameEngine([bot1, bot2], verbose=False)
        
        # Setup
        game.setup_game = lambda: None
        game.bots = [bot1, bot2]
        bot1.hand = [Card(CardType.FAVOR)]
        bot2.hand = [Card(CardType.SKIP)]
        bot1.alive = True
        bot2.alive = True
        
        # Clear notifications
        bot1.notifications = []
        bot2.notifications = []
        
        # Execute Favor
        game._execute_favor(bot1)
        
        # Both should be notified about the card transfer
        # There should be notifications for both the Favor play and the result
        self.assertGreaterEqual(len(bot1.notifications), 1)
        self.assertGreaterEqual(len(bot2.notifications), 1)
        
        # Check for "gives" in notifications
        all_actions = [n['action'] for n in bot1.notifications + bot2.notifications]
        self.assertTrue(any("gives" in action for action in all_actions))


class TestReplayRecorder(unittest.TestCase):
    """Test ReplayRecorder class."""
    
    def test_replay_recorder_creation(self):
        """Test creating a replay recorder."""
        from game import ReplayRecorder
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=True)
        self.assertTrue(recorder.enabled)
        self.assertEqual(len(recorder.events), 0)
        self.assertIsNone(recorder.winner)
    
    def test_replay_recorder_disabled(self):
        """Test that disabled recorder doesn't record events."""
        from game import ReplayRecorder
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=False)
        recorder.record_card_play("Bot1", CardType.SKIP, False)
        self.assertEqual(len(recorder.events), 0)
    
    def test_replay_recorder_game_setup(self):
        """Test recording game setup."""
        from game import ReplayRecorder
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=True)
        initial_hands = {
            "Bot1": ["Defuse", "Skip", "Attack"],
            "Bot2": ["Defuse", "Nope", "Shuffle"]
        }
        recorder.record_game_setup(20, 7, ["Bot1", "Bot2"], initial_hands=initial_hands)
        self.assertEqual(len(recorder.events), 1)
        self.assertEqual(recorder.events[0]["type"], "game_setup")
        self.assertEqual(recorder.events[0]["deck_size"], 20)
        self.assertIn("initial_hands", recorder.events[0])
        self.assertEqual(recorder.events[0]["initial_hands"]["Bot1"], ["Defuse", "Skip", "Attack"])
    
    def test_replay_recorder_card_play(self):
        """Test recording card plays."""
        from game import ReplayRecorder
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=True)
        recorder.record_card_play("Bot1", CardType.SKIP, False)
        self.assertEqual(len(recorder.events), 1)
        self.assertEqual(recorder.events[0]["type"], "card_play")
        self.assertEqual(recorder.events[0]["player"], "Bot1")
        self.assertEqual(recorder.events[0]["card"], "Skip")
        self.assertFalse(recorder.events[0]["was_noped"])
    
    def test_replay_recorder_combo_play(self):
        """Test recording combo plays."""
        from game import ReplayRecorder
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=True)
        recorder.record_combo_play("Bot1", "2-of-a-kind", 
                                   [CardType.TACOCAT, CardType.TACOCAT],
                                   target="Bot2", was_noped=False)
        self.assertEqual(len(recorder.events), 1)
        self.assertEqual(recorder.events[0]["type"], "combo_play")
        self.assertEqual(recorder.events[0]["combo_type"], "2-of-a-kind")
        self.assertEqual(recorder.events[0]["target"], "Bot2")
    
    def test_replay_recorder_to_json(self):
        """Test converting replay to JSON."""
        from game import ReplayRecorder
        import json
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=True)
        recorder.record_game_setup(20, 7, ["Bot1", "Bot2"])
        recorder.record_game_end("Bot1")
        
        json_str = recorder.to_json()
        data = json.loads(json_str)
        
        self.assertIn("metadata", data)
        self.assertIn("events", data)
        self.assertIn("winner", data)
        self.assertEqual(data["winner"], "Bot1")
        self.assertEqual(len(data["events"]), 2)
    
    def test_game_with_replay_recorder(self):
        """Test that game engine works with replay recorder."""
        from game import ReplayRecorder
        bot1 = SimpleBot("Bot1")
        bot2 = SimpleBot("Bot2")
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=True)
        
        game = GameEngine([bot1, bot2], verbose=False, replay_recorder=recorder)
        winner = game.play_game()
        
        # Check that events were recorded
        self.assertGreater(len(recorder.events), 0)
        self.assertIsNotNone(recorder.winner)
        
        # Verify game_setup event exists
        setup_events = [e for e in recorder.events if e["type"] == "game_setup"]
        self.assertEqual(len(setup_events), 1)
        
        # Verify game_end event exists
        end_events = [e for e in recorder.events if e["type"] == "game_end"]
        self.assertEqual(len(end_events), 1)
    
    def test_replay_recorder_turn_start(self):
        """Test recording turn start."""
        from game import ReplayRecorder
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=True)
        recorder.record_turn_start("Bot1", 1, 1, 7, 20)
        self.assertEqual(len(recorder.events), 1)
        self.assertEqual(recorder.events[0]["type"], "turn_start")
        self.assertEqual(recorder.events[0]["turn_number"], 1)
    
    def test_replay_recorder_exploding_kitten(self):
        """Test recording exploding kitten events."""
        from game import ReplayRecorder
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=True)
        recorder.record_exploding_kitten_draw("Bot1", True)
        recorder.record_defuse("Bot1", 5)
        
        self.assertEqual(len(recorder.events), 2)
        self.assertEqual(recorder.events[0]["type"], "exploding_kitten_draw")
        self.assertTrue(recorder.events[0]["had_defuse"])
        self.assertEqual(recorder.events[1]["type"], "defuse")
        self.assertEqual(recorder.events[1]["insert_position"], 5)
    
    def test_replay_recorder_player_elimination(self):
        """Test recording player elimination."""
        from game import ReplayRecorder
        recorder = ReplayRecorder(["Bot1", "Bot2"], enabled=True)
        recorder.record_player_elimination("Bot1")
        
        self.assertEqual(len(recorder.events), 1)
        self.assertEqual(recorder.events[0]["type"], "player_elimination")
        self.assertEqual(recorder.events[0]["player"], "Bot1")


if __name__ == '__main__':
    unittest.main()

