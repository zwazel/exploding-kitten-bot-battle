"""Game engine for Exploding Kittens bot battle."""

import random
from typing import List, Optional
from .bot import Bot
from .deck import Deck
from .cards import Card, CardType
from .game_state import GameState, CardCounts


class GameEngine:
    """Main game engine that runs the Exploding Kittens game."""

    def __init__(self, bots: List[Bot], verbose: bool = True):
        """
        Initialize the game engine.
        
        Args:
            bots: List of bots to play the game
            verbose: Whether to print game events
        """
        if len(bots) < 2:
            raise ValueError("Need at least 2 bots to play")
        
        self.bots = bots
        self.verbose = verbose
        self.deck = Deck(len(bots))
        self.game_state = GameState(
            total_cards_in_deck=CardCounts(),
            cards_left_to_draw=0,
            was_last_card_exploding_kitten=False,
            history_of_played_cards=[],
            alive_bots=len(bots)
        )
        self.current_bot_index = 0
        self.turns_to_take = 1  # For Attack cards
        
    def _log(self, message: str) -> None:
        """Print a message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def setup_game(self) -> None:
        """Set up the initial game state."""
        self._log("=" * 60)
        self._log("Setting up Exploding Kittens game...")
        self._log(f"Players: {', '.join(bot.name for bot in self.bots)}")
        self._log("=" * 60)
        
        # Deal initial hands (7 cards per player, including 1 Defuse)
        for bot in self.bots:
            # Each player gets 1 Defuse card guaranteed
            defuse_card = None
            for i, card in enumerate(self.deck.draw_pile):
                if card.card_type == CardType.DEFUSE:
                    defuse_card = self.deck.draw_pile.pop(i)
                    break
            
            if defuse_card:
                bot.add_card(defuse_card)
            
            # Deal remaining cards
            for _ in range(6):
                if self.deck.size() > 0:
                    card = self.deck.draw()
                    bot.add_card(card)
        
        # Add Exploding Kittens to the deck (num_players - 1)
        num_exploding_kittens = len(self.bots) - 1
        for _ in range(num_exploding_kittens):
            self.deck.add_to_bottom(Card(CardType.EXPLODING_KITTEN))
        
        # Shuffle the deck
        self.deck.shuffle()
        
        # Update game state
        self.game_state.total_cards_in_deck = self.deck.get_total_card_counts()
        self.game_state.cards_left_to_draw = self.deck.size()
        self.game_state.alive_bots = len([b for b in self.bots if b.alive])
        
        # Randomize play order
        random.shuffle(self.bots)
        
        self._log(f"\nDeck ready with {self.deck.size()} cards")
        self._log(f"Each player has 7 cards (including 1 Defuse)")
        self._log(f"Play order: {', '.join(bot.name for bot in self.bots)}\n")

    def play_game(self) -> Optional[Bot]:
        """
        Play the game until there's a winner.
        
        Returns:
            The winning bot, or None if no winner
        """
        self.setup_game()
        
        turn_count = 0
        max_turns = 1000  # Prevent infinite loops
        
        while self.game_state.alive_bots > 1 and turn_count < max_turns:
            turn_count += 1
            current_bot = self.bots[self.current_bot_index]
            
            # Skip dead bots
            if not current_bot.alive:
                self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
                continue
            
            self._log(f"\n{'=' * 60}")
            self._log(f"Turn {turn_count}: {current_bot.name}'s turn")
            self._log(f"Hand ({len(current_bot.hand)} cards): {', '.join(str(c) for c in current_bot.hand)}")
            self._log(f"Cards left in deck: {self.deck.size()}")
            
            # Play phase: Bot can play cards before drawing
            self._play_phase(current_bot)
            
            # Draw phase: Bot must draw a card
            if current_bot.alive:
                self._draw_phase(current_bot)
            
            # Move to next bot if no attack card was played
            if self.turns_to_take <= 0:
                self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
                self.turns_to_take = 1
            else:
                self.turns_to_take -= 1
        
        # Find the winner
        alive_bots = [bot for bot in self.bots if bot.alive]
        if alive_bots:
            winner = alive_bots[0]
            self._log(f"\n{'=' * 60}")
            self._log(f"🎉 GAME OVER! Winner: {winner.name} 🎉")
            self._log(f"{'=' * 60}\n")
            return winner
        
        return None

    def _play_phase(self, bot: Bot) -> None:
        """
        Handle the play phase where a bot can play cards.
        
        Args:
            bot: The bot whose turn it is
        """
        while True:
            try:
                card_to_play = bot.play(self.game_state.copy())
                
                if card_to_play is None:
                    self._log(f"{bot.name} ends play phase")
                    break
                
                # Validate the bot has the card
                if not bot.has_card(card_to_play):
                    self._log(f"WARNING: {bot.name} tried to play a card they don't have!")
                    break
                
                # Play the card
                self._handle_card_play(bot, card_to_play)
                
                # Some cards end the turn
                if card_to_play.card_type == CardType.SKIP:
                    break
                    
            except Exception as e:
                self._log(f"ERROR: {bot.name} raised exception during play phase: {e}")
                break

    def _handle_card_play(self, bot: Bot, card: Card) -> None:
        """
        Handle a card being played.
        
        Args:
            bot: The bot playing the card
            card: The card being played
        """
        self._log(f"{bot.name} plays {card}")
        bot.remove_card(card)
        self.game_state.history_of_played_cards.append(card)
        
        # Handle card effects
        if card.card_type == CardType.SKIP:
            self._log("  → Skip: Turn ends without drawing")
            self.turns_to_take = 0
        elif card.card_type == CardType.SEE_THE_FUTURE:
            top_three = self.deck.peek(3)
            self._log(f"  → See the Future: {', '.join(str(c) for c in top_three)}")
            try:
                bot.see_the_future(self.game_state.copy(), top_three)
            except Exception as e:
                self._log(f"  ERROR: {bot.name} raised exception in see_the_future: {e}")
        elif card.card_type == CardType.SHUFFLE:
            self._log("  → Shuffle: Deck shuffled")
            self.deck.shuffle()
        elif card.card_type == CardType.ATTACK:
            self._log("  → Attack: Next player takes 2 turns")
            self.turns_to_take = 0  # Current bot ends turn
            # Next bot will take 2 turns (handled in main loop)
        # Other cards (Favor, Nope, Cat) would be implemented in full version

    def _draw_phase(self, bot: Bot) -> None:
        """
        Handle the draw phase where a bot must draw a card.
        
        Args:
            bot: The bot drawing a card
        """
        if self.deck.size() == 0:
            self._log(f"Deck is empty! {bot.name} survives!")
            return
        
        self._log(f"{bot.name} draws a card...")
        drawn_card = self.deck.draw()
        self.game_state.cards_left_to_draw = self.deck.size()
        self.game_state.was_last_card_exploding_kitten = False
        
        if drawn_card.card_type == CardType.EXPLODING_KITTEN:
            self._log(f"  💣 {bot.name} drew an EXPLODING KITTEN!")
            self._handle_exploding_kitten(bot, drawn_card)
        else:
            self._log(f"  → Drew: {drawn_card}")
            bot.add_card(drawn_card)

    def _handle_exploding_kitten(self, bot: Bot, exploding_kitten: Card) -> None:
        """
        Handle a bot drawing an Exploding Kitten.
        
        Args:
            bot: The bot that drew the Exploding Kitten
            exploding_kitten: The Exploding Kitten card
        """
        # Check if bot has a Defuse card
        has_defuse = bot.has_card_type(CardType.DEFUSE)
        
        if has_defuse:
            self._log(f"  {bot.name} has a Defuse card!")
            
            # Remove Defuse card from hand
            defuse_card = next(c for c in bot.hand if c.card_type == CardType.DEFUSE)
            bot.remove_card(defuse_card)
            self.game_state.history_of_played_cards.append(defuse_card)
            
            # Ask bot where to put the Exploding Kitten
            try:
                position = bot.handle_exploding_kitten(self.game_state.copy())
                position = max(0, min(position, self.deck.size()))
                self.deck.insert_at(exploding_kitten, position)
                self._log(f"  → Defused! Exploding Kitten inserted at position {position}")
                self.game_state.was_last_card_exploding_kitten = True
            except Exception as e:
                self._log(f"  ERROR: {bot.name} raised exception in handle_exploding_kitten: {e}")
                # Default: put it back on top
                self.deck.add_to_top(exploding_kitten)
                self._log(f"  → Defused! Exploding Kitten placed on top (default)")
                self.game_state.was_last_card_exploding_kitten = True
        else:
            self._log(f"  💀 {bot.name} has no Defuse card and EXPLODES!")
            bot.alive = False
            self.game_state.alive_bots -= 1
            self.game_state.history_of_played_cards.append(exploding_kitten)
            self.game_state.was_last_card_exploding_kitten = False
