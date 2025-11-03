"""Game engine for Exploding Kittens bot battle."""

import random
from typing import List, Optional, Tuple, Union
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
    
    def _get_alive_bots_except(self, exclude_bot: Bot) -> List[Bot]:
        """Get list of alive bots excluding the specified bot."""
        return [b for b in self.bots if b.alive and b != exclude_bot]
    
    def _get_bots_in_play_order_after(self, after_bot: Bot) -> List[Bot]:
        """
        Get bots in play order starting after the specified bot.
        
        Args:
            after_bot: The bot to start after
            
        Returns:
            List of all bots in play order, starting from the one after after_bot
        """
        # Find the index of after_bot
        try:
            start_index = self.bots.index(after_bot)
        except ValueError:
            return self.bots.copy()
        
        # Create list starting from next bot and wrapping around
        result = []
        for i in range(1, len(self.bots)):
            next_index = (start_index + i) % len(self.bots)
            result.append(self.bots[next_index])
        
        return result
    
    def _check_for_nope(self, action_description: str, initiator: Bot) -> bool:
        """
        Check if any player wants to play a Nope card in play order. Can be chained.
        Each action is announced to all players in turn order before they can respond.
        
        Args:
            action_description: Description of the action being played
            initiator: The bot who initiated the action
            
        Returns:
            True if action is noped (odd number of nopes), False otherwise
        """
        nope_count = 0
        current_action = action_description
        last_actor = initiator
        
        while True:
            noped = False
            # Notify bots in play order starting from the one after last_actor
            bots_in_order = self._get_bots_in_play_order_after(last_actor)
            
            for bot in bots_in_order:
                if not bot.alive:
                    continue
                
                # Notify bot about the action
                self._log(f"  → Notifying {bot.name} about: {current_action}")
                
                # Check if bot wants to play Nope
                if bot.has_card_type(CardType.NOPE):
                    try:
                        if bot.should_play_nope(self.game_state.copy(), current_action):
                            # Bot wants to play Nope
                            nope_card = next(c for c in bot.hand if c.card_type == CardType.NOPE)
                            bot.remove_card(nope_card)
                            self.deck.discard_pile.append(nope_card)
                            nope_count += 1
                            last_actor = bot
                            self._log(f"  🚫 {bot.name} plays NOPE! (Nope #{nope_count})")
                            
                            # Update action description for next round
                            current_action = f"{bot.name} playing NOPE on: {current_action}"
                            noped = True
                            break
                    except Exception as e:
                        self._log(f"  ERROR: {bot.name} raised exception in should_play_nope: {e}")
            
            if not noped:
                break
        
        # Odd number of nopes = action is canceled
        if nope_count > 0:
            if nope_count % 2 == 1:
                self._log(f"  ❌ Action NOPED! ({nope_count} Nope(s) played)")
                return True
            else:
                self._log(f"  ✓ Action proceeds ({nope_count} Nope(s) played)")
        
        return False
    
    def _is_valid_combo(self, cards: List[Card]) -> Optional[str]:
        """
        Check if cards form a valid combo.
        
        Returns:
            Combo type ("2-of-a-kind", "3-of-a-kind", "5-unique") or None if invalid
        """
        if len(cards) == 2:
            if cards[0].card_type == cards[1].card_type:
                return "2-of-a-kind"
        elif len(cards) == 3:
            if cards[0].card_type == cards[1].card_type == cards[2].card_type:
                return "3-of-a-kind"
        elif len(cards) == 5:
            types = set(c.card_type for c in cards)
            if len(types) == 5:
                return "5-unique"
        return None

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
            
            # Draw phase: Bot must draw a card (unless Skip or Attack was played)
            if current_bot.alive and self.turns_to_take > 0:
                self._draw_phase(current_bot)
            
            # Decrement turns for this player
            self.turns_to_take -= 1
            
            # Move to next bot when current bot has no more turns
            if self.turns_to_take <= 0:
                self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
                if self.turns_to_take == -1:
                    # Attack was played, next player takes 2 turns
                    self.turns_to_take = 2
                else:
                    # Normal turn
                    self.turns_to_take = 1
        
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
        Handle the play phase where a bot can play cards or combos.
        
        Args:
            bot: The bot whose turn it is
        """
        while True:
            try:
                play_result = bot.play(self.game_state.copy())
                
                if play_result is None:
                    self._log(f"{bot.name} ends play phase")
                    break
                
                # Check if it's a combo (list of cards) or single card
                if isinstance(play_result, list):
                    # Playing a combo
                    self._handle_combo(bot, play_result)
                else:
                    # Playing a single card
                    # Validate the bot has the card
                    if not bot.has_card(play_result):
                        self._log(f"WARNING: {bot.name} tried to play a card they don't have!")
                        break
                    
                    # Play the card
                    self._handle_card_play(bot, play_result)
                    
                    # Some cards end the turn
                    if play_result.card_type == CardType.SKIP:
                        break
                    
            except Exception as e:
                self._log(f"ERROR: {bot.name} raised exception during play phase: {e}")
                break
    
    def _handle_combo(self, bot: Bot, cards: List[Card]) -> None:
        """
        Handle a combo being played.
        
        Args:
            bot: The bot playing the combo
            cards: List of cards in the combo
        """
        # Validate bot has all cards
        for card in cards:
            if not bot.has_card(card):
                self._log(f"WARNING: {bot.name} tried to play a combo with cards they don't have!")
                return
        
        # Check if valid combo
        combo_type = self._is_valid_combo(cards)
        if not combo_type:
            self._log(f"WARNING: {bot.name} tried to play invalid combo!")
            return
        
        self._log(f"{bot.name} plays {combo_type} combo: {', '.join(str(c) for c in cards)}")
        
        # Remove cards from hand and add to discard
        for card in cards:
            bot.remove_card(card)
            self.deck.discard_pile.append(card)
        
        # Check for Nope
        action_desc = f"{bot.name} playing {combo_type} combo"
        if self._check_for_nope(action_desc, bot):
            return  # Combo was noped
        
        # Execute combo effect
        if combo_type == "2-of-a-kind":
            self._execute_2_of_a_kind(bot)
        elif combo_type == "3-of-a-kind":
            self._execute_3_of_a_kind(bot)
        elif combo_type == "5-unique":
            self._execute_5_unique(bot)
    
    def _execute_2_of_a_kind(self, bot: Bot) -> None:
        """Execute 2-of-a-kind combo: randomly steal a card from target."""
        alive_others = self._get_alive_bots_except(bot)
        if not alive_others:
            self._log(f"  → No targets available")
            return
        
        try:
            target = bot.choose_target(self.game_state.copy(), alive_others)
            if target and target.hand:
                stolen_card = random.choice(target.hand)
                target.remove_card(stolen_card)
                bot.add_card(stolen_card)
                self._log(f"  → {bot.name} randomly steals {stolen_card} from {target.name}")
            else:
                self._log(f"  → Target has no cards")
        except Exception as e:
            self._log(f"  ERROR: {bot.name} raised exception in choose_target: {e}")
    
    def _execute_3_of_a_kind(self, bot: Bot) -> None:
        """Execute 3-of-a-kind combo: request specific card type from target."""
        alive_others = self._get_alive_bots_except(bot)
        if not alive_others:
            self._log(f"  → No targets available")
            return
        
        try:
            target = bot.choose_target(self.game_state.copy(), alive_others)
            if not target:
                return
            
            requested_type = bot.choose_card_type(self.game_state.copy())
            if not requested_type:
                return
            
            # Check if target has that card type
            matching_cards = [c for c in target.hand if c.card_type == requested_type]
            if matching_cards:
                card_to_give = matching_cards[0]
                target.remove_card(card_to_give)
                bot.add_card(card_to_give)
                self._log(f"  → {bot.name} requests {requested_type.value} from {target.name} and receives {card_to_give}")
            else:
                self._log(f"  → {target.name} doesn't have {requested_type.value}")
        except Exception as e:
            self._log(f"  ERROR: {bot.name} raised exception: {e}")
    
    def _execute_5_unique(self, bot: Bot) -> None:
        """Execute 5-unique combo: take any card from discard pile."""
        if not self.deck.discard_pile:
            self._log(f"  → Discard pile is empty")
            return
        
        try:
            chosen_card = bot.choose_from_discard(self.game_state.copy(), self.deck.discard_pile.copy())
            if chosen_card and chosen_card in self.deck.discard_pile:
                self.deck.discard_pile.remove(chosen_card)
                bot.add_card(chosen_card)
                self._log(f"  → {bot.name} takes {chosen_card} from discard pile")
            else:
                self._log(f"  → Invalid card selection from discard")
        except Exception as e:
            self._log(f"  ERROR: {bot.name} raised exception in choose_from_discard: {e}")

    def _handle_card_play(self, bot: Bot, card: Card) -> None:
        """
        Handle a single card being played.
        
        Args:
            bot: The bot playing the card
            card: The card being played
        """
        self._log(f"{bot.name} plays {card}")
        bot.remove_card(card)
        self.deck.discard_pile.append(card)
        
        # Handle card effects
        if card.card_type == CardType.SKIP:
            # Check for Nope
            if self._check_for_nope(f"{bot.name} playing Skip", bot):
                return
            self._log("  → Skip: Turn ends without drawing")
            self.turns_to_take = 0
        elif card.card_type == CardType.SEE_THE_FUTURE:
            # Check for Nope
            if self._check_for_nope(f"{bot.name} playing See the Future", bot):
                return
            top_three = self.deck.peek(3)
            self._log(f"  → See the Future: {', '.join(str(c) for c in top_three)}")
            try:
                bot.see_the_future(self.game_state.copy(), top_three)
            except Exception as e:
                self._log(f"  ERROR: {bot.name} raised exception in see_the_future: {e}")
        elif card.card_type == CardType.SHUFFLE:
            # Check for Nope
            if self._check_for_nope(f"{bot.name} playing Shuffle", bot):
                return
            self._log("  → Shuffle: Deck shuffled")
            self.deck.shuffle()
        elif card.card_type == CardType.ATTACK:
            # Check for Nope
            if self._check_for_nope(f"{bot.name} playing Attack", bot):
                return
            self._log("  → Attack: Next player takes 2 turns")
            self.turns_to_take = -1  # End turn without drawing, next player gets 2 turns
        elif card.card_type == CardType.FAVOR:
            # Check for Nope
            if self._check_for_nope(f"{bot.name} playing Favor", bot):
                return
            self._execute_favor(bot)
        elif card.card_type == CardType.NOPE:
            self._log("  → Nope can only be played in response to actions")
        # Cat cards have no effect when played alone
    
    def _execute_favor(self, bot: Bot) -> None:
        """Execute Favor card: target chooses what card to give."""
        alive_others = self._get_alive_bots_except(bot)
        if not alive_others:
            self._log(f"  → No targets available for Favor")
            return
        
        try:
            target = bot.choose_target(self.game_state.copy(), alive_others)
            if not target or not target.hand:
                self._log(f"  → Target has no cards")
                return
            
            # Target chooses which card to give
            card_to_give = target.choose_card_from_hand(self.game_state.copy())
            if card_to_give and target.has_card(card_to_give):
                target.remove_card(card_to_give)
                bot.add_card(card_to_give)
                self._log(f"  → {target.name} gives {card_to_give} to {bot.name}")
            else:
                self._log(f"  ERROR: {target.name} tried to give invalid card")
        except Exception as e:
            self._log(f"  ERROR: Exception in Favor execution: {e}")

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
