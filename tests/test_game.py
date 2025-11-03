"""Tests for the Exploding Kittens game components."""

import unittest
from game import Card, CardType, GameState, CardCounts, Bot, Deck, GameEngine
from typing import Optional, List


class SimpleBot(Bot):
    """A simple test bot for testing purposes."""
    
    def play(self, state: GameState) -> Optional[Card]:
        return None
    
    def handle_exploding_kitten(self, state: GameState) -> int:
        return 0
    
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        pass


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
        counts = CardCounts(exploding_kitten=2, defuse=4)
        state = GameState(
            total_cards_in_deck=counts,
            cards_left_to_draw=10,
            was_last_card_exploding_kitten=False,
            alive_bots=3
        )
        self.assertEqual(state.cards_left_to_draw, 10)
        self.assertEqual(state.alive_bots, 3)
        self.assertFalse(state.was_last_card_exploding_kitten)
    
    def test_game_state_copy(self):
        """Test copying game state."""
        state = GameState(
            total_cards_in_deck=CardCounts(),
            cards_left_to_draw=5,
            was_last_card_exploding_kitten=True,
            alive_bots=2
        )
        copy = state.copy()
        self.assertEqual(copy.cards_left_to_draw, state.cards_left_to_draw)
        self.assertEqual(copy.alive_bots, state.alive_bots)


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


if __name__ == '__main__':
    unittest.main()

