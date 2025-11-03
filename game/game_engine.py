"""Game engine for Exploding Kittens bot battle."""

import random
from typing import List, Optional, Tuple, Union, Dict
from .bot import Bot
from .deck import Deck
from .cards import Card, CardType, ComboType, TargetContext
from .game_state import GameState


class GameEngine:
    """Main game engine that runs the Exploding Kittens game."""

    def __init__(self, bots: List[Bot], verbose: bool = True, deck_config: Dict[CardType, int] = None):
        """
        Initialize the game engine.
        
        Args:
            bots: List of bots to play the game
            verbose: Whether to print game events
            deck_config: Optional custom deck configuration
        """
        if len(bots) < 2:
            raise ValueError("Need at least 2 bots to play")
        
        self.bots = bots
        self.verbose = verbose
        self.deck = Deck(len(bots), deck_config)
        self.game_state = GameState(
            initial_card_counts={},
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
    
    def _notify_all_bots(self, action_description: str, actor: Bot) -> None:
        """
        Notify all alive bots about an action.
        
        Args:
            action_description: Description of the action
            actor: The bot who performed the action
        """
        # Notify ALL bots in play order (including the actor)
        # Start from the bot after the actor
        bots_in_order = self._get_bots_in_play_order_after(actor)
        
        for bot in bots_in_order:
            if not bot.alive:
                continue
            
            self._log(f"  → Notifying {bot.name} about: {action_description}")
            try:
                bot.on_action_played(self.game_state.copy(), action_description, actor)
            except Exception as e:
                self._log(f"  ERROR: {bot.name} raised exception in on_action_played: {e}")
        
        # Also notify the actor themselves
        if actor.alive:
            self._log(f"  → Notifying {actor.name} about: {action_description}")
            try:
                actor.on_action_played(self.game_state.copy(), action_description, actor)
            except Exception as e:
                self._log(f"  ERROR: {actor.name} raised exception in on_action_played: {e}")
    
    def _check_for_nope(self, action_description: str, initiator: Bot) -> bool:
        """
        Check if any player wants to play a Nope card in play order. Can be chained.
        First notifies all players about the action, then checks for Nopes.
        When someone Nopes, notify everyone about the Nope, then check again.
        
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
            # FIRST: Notify all bots about the current action
            self._notify_all_bots(current_action, last_actor)
            
            # SECOND: Check if anyone wants to Nope
            noped = False
            bots_in_order = self._get_bots_in_play_order_after(last_actor)
            
            for bot in bots_in_order:
                if not bot.alive:
                    continue
                
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
                            break  # Stop checking, go to notification phase for this Nope
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
    
    def _is_valid_combo(self, cards: List[Card]) -> Optional[ComboType]:
        """
        Check if cards form a valid combo.
        
        Returns:
            ComboType enum value if valid combo, None if invalid
        """
        # Exploding Kitten and Defuse cannot be used in combos
        for card in cards:
            if card.card_type in [CardType.EXPLODING_KITTEN, CardType.DEFUSE]:
                return None
        
        if len(cards) == 2:
            if cards[0].card_type == cards[1].card_type:
                return ComboType.TWO_OF_A_KIND
        elif len(cards) == 3:
            if cards[0].card_type == cards[1].card_type == cards[2].card_type:
                return ComboType.THREE_OF_A_KIND
        elif len(cards) == 5:
            types = set(c.card_type for c in cards)
            if len(types) == 5:
                return ComboType.FIVE_UNIQUE
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
        
        # Update game state with initial card counts
        self.game_state.initial_card_counts = self.deck.get_initial_card_counts()
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
            current_bot = self.bots[self.current_bot_index]
            
            # Skip dead bots
            if not current_bot.alive:
                self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
                self.turns_to_take = 1
                continue
            
            # Process all turns for current bot
            while self.turns_to_take > 0 and current_bot.alive:
                turn_count += 1
                
                self._log(f"\n{'=' * 60}")
                self._log(f"Turn {turn_count}: {current_bot.name}'s turn ({self.turns_to_take} turn(s) total)")
                self._log(f"Hand ({len(current_bot.hand)} cards): {', '.join(str(c) for c in current_bot.hand)}")
                self._log(f"Cards left in deck: {self.deck.size()}")
                
                # Play phase: Bot can play cards before drawing
                turn_ended_by_card = self._play_phase(current_bot)
                
                if turn_ended_by_card:
                    # Attack or Skip was played
                    if self.turns_to_take < 0:
                        # Attack was played - all turns ended
                        self._log(f"→ Attack played - {current_bot.name}'s all turns end")
                        break
                    else:
                        # Skip was played - one turn ended
                        self._log(f"→ Skip played - one turn skipped")
                        self.turns_to_take -= 1
                        if self.turns_to_take > 0:
                            self._log(f"→ {current_bot.name} has {self.turns_to_take} turn(s) remaining")
                else:
                    # Must draw a card
                    if current_bot.alive:
                        self._draw_phase(current_bot)
                        self.turns_to_take -= 1
                        if self.turns_to_take > 0 and current_bot.alive:
                            self._log(f"→ {current_bot.name} has {self.turns_to_take} turn(s) remaining")
            
            # Move to next bot
            self.current_bot_index = (self.current_bot_index + 1) % len(self.bots)
            if self.turns_to_take < 0:
                # Attack was played, next player gets the absolute value
                self.turns_to_take = abs(self.turns_to_take)
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

    def _play_phase(self, bot: Bot) -> bool:
        """
        Handle the play phase where a bot can play cards or combos.
        
        Args:
            bot: The bot whose turn it is
            
        Returns:
            True if turn should end (Attack or Skip played), False otherwise
        """
        max_attempts = 100  # Prevent infinite loops
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            try:
                play_result = bot.play(self.game_state.copy())
                
                if play_result is None:
                    self._log(f"{bot.name} ends play phase")
                    return False  # Turn doesn't end, will draw
                
                # Check if it's a combo (list of cards) or single card
                if isinstance(play_result, list):
                    # Playing a combo
                    self._handle_combo(bot, play_result)
                    # Continue loop to allow playing more cards
                else:
                    # Playing a single card
                    # Validate the bot has the card
                    if not bot.has_card(play_result):
                        self._log(f"WARNING: {bot.name} tried to play a card they don't have!")
                        return False
                    
                    # Play the card
                    card_type = play_result.card_type
                    card_executed = self._handle_card_play(bot, play_result)
                    
                    # Attack ends ALL remaining turns (if not noped)
                    if card_executed and card_type == CardType.ATTACK:
                        return True
                    
                    # Skip ends ONE turn (if not noped)
                    if card_executed and card_type == CardType.SKIP:
                        return True
                    
            except Exception as e:
                self._log(f"ERROR: {bot.name} raised exception during play phase: {e}")
                return False
        
        # If max attempts reached, end play phase
        self._log(f"WARNING: {bot.name} reached max play attempts, ending phase")
        return False
    
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
        
        self._log(f"{bot.name} plays {combo_type.value} combo: {', '.join(str(c) for c in cards)}")
        
        # Remove cards from hand and add to discard
        for card in cards:
            bot.remove_card(card)
            self.deck.discard_pile.append(card)
        
        # For combos that require a target, select target first before Nope check
        target = None
        if combo_type in [ComboType.TWO_OF_A_KIND, ComboType.THREE_OF_A_KIND]:
            alive_others = self._get_alive_bots_except(bot)
            if not alive_others:
                self._log(f"  → No targets available")
                return
            
            try:
                # Map combo type to target context
                context = TargetContext.TWO_OF_A_KIND if combo_type == ComboType.TWO_OF_A_KIND else TargetContext.THREE_OF_A_KIND
                target = bot.choose_target(self.game_state.copy(), alive_others, context)
                if not target:
                    self._log(f"  → No target selected")
                    return
                self._log(f"  → {bot.name} targets {target.name}")
            except Exception as e:
                self._log(f"  ERROR: {bot.name} raised exception in choose_target: {e}")
                return
        
        # Check for Nope with target information
        if combo_type in [ComboType.TWO_OF_A_KIND, ComboType.THREE_OF_A_KIND]:
            action_desc = f"{bot.name} playing {combo_type.value} combo targeting {target.name}"
        else:
            action_desc = f"{bot.name} playing {combo_type.value} combo"
        
        if self._check_for_nope(action_desc, bot):
            return  # Combo was noped
        
        # Execute combo effect
        if combo_type == ComboType.TWO_OF_A_KIND:
            self._execute_2_of_a_kind_with_target(bot, target)
        elif combo_type == ComboType.THREE_OF_A_KIND:
            self._execute_3_of_a_kind_with_target(bot, target)
        elif combo_type == ComboType.FIVE_UNIQUE:
            self._execute_5_unique(bot)
    
    def _execute_2_of_a_kind_with_target(self, bot: Bot, target: Bot) -> None:
        """Execute 2-of-a-kind combo with pre-selected target: randomly steal a card."""
        if not target.hand:
            self._log(f"  → {target.name} has no cards")
            self._notify_all_bots(f"{bot.name}'s 2-of-a-kind combo failed (target has no cards)", bot)
            return
        
        stolen_card = random.choice(target.hand)
        target.remove_card(stolen_card)
        bot.add_card(stolen_card)
        # Show full details in user-facing logs (bots don't get this info in GameState)
        self._log(f"  → {bot.name} randomly steals {stolen_card} from {target.name}")
        # Notify bots (they don't know which specific card, just that a card was stolen)
        self._notify_all_bots(f"{bot.name} steals a card from {target.name}", bot)
    
    def _execute_3_of_a_kind_with_target(self, bot: Bot, target: Bot) -> None:
        """Execute 3-of-a-kind combo with pre-selected target: request specific card type."""
        try:
            requested_type = bot.choose_card_type(self.game_state.copy())
            if not requested_type:
                return
            
            # Loudly announce the requested card type (everyone knows)
            self._log(f"  → {bot.name} requests {requested_type.value} from {target.name}")
            # Notify all bots about the request (public announcement)
            self._notify_all_bots(f"{bot.name} requests {requested_type.value} from {target.name}", bot)
            
            # Check if target has that card type
            matching_cards = [c for c in target.hand if c.card_type == requested_type]
            if matching_cards:
                card_to_give = matching_cards[0]
                target.remove_card(card_to_give)
                bot.add_card(card_to_give)
                # Everyone knows the request succeeded
                self._log(f"  → {target.name} gives {requested_type.value} to {bot.name}")
                self._notify_all_bots(f"{target.name} gives {requested_type.value} to {bot.name}", bot)
            else:
                self._log(f"  → {target.name} doesn't have {requested_type.value}")
                self._notify_all_bots(f"{target.name} doesn't have {requested_type.value}", bot)
        except Exception as e:
            self._log(f"  ERROR: {bot.name} raised exception: {e}")
    
    def _execute_5_unique(self, bot: Bot) -> None:
        """Execute 5-unique combo: take any card from discard pile."""
        if not self.deck.discard_pile:
            self._log(f"  → Discard pile is empty")
            self._notify_all_bots(f"{bot.name}'s 5-unique combo failed (discard pile empty)", bot)
            return
        
        try:
            chosen_card = bot.choose_from_discard(self.game_state.copy(), self.deck.discard_pile.copy())
            if chosen_card and chosen_card in self.deck.discard_pile:
                self.deck.discard_pile.remove(chosen_card)
                bot.add_card(chosen_card)
                self._log(f"  → {bot.name} takes {chosen_card} from discard pile")
                # Notify all bots (this is public information)
                self._notify_all_bots(f"{bot.name} takes {chosen_card.card_type.value} from discard pile", bot)
            else:
                self._log(f"  → Invalid card selection from discard")
                self._notify_all_bots(f"{bot.name}'s 5-unique combo failed (invalid selection)", bot)
        except Exception as e:
            self._log(f"  ERROR: {bot.name} raised exception in choose_from_discard: {e}")

    def _handle_card_play(self, bot: Bot, card: Card) -> bool:
        """
        Handle a single card being played.
        
        Args:
            bot: The bot playing the card
            card: The card being played
            
        Returns:
            True if card effect was executed (not noped), False if noped
        """
        self._log(f"{bot.name} plays {card}")
        bot.remove_card(card)
        self.deck.discard_pile.append(card)
        
        # Handle card effects
        if card.card_type == CardType.SKIP:
            # Check for Nope
            if self._check_for_nope(f"{bot.name} playing Skip", bot):
                return False
            self._log("  → Skip: Skips one turn without drawing")
            # Skip is handled in _play_phase by returning True
            return True
        elif card.card_type == CardType.SEE_THE_FUTURE:
            # Check for Nope
            if self._check_for_nope(f"{bot.name} playing See the Future", bot):
                return False
            top_three = self.deck.peek(3)
            # Show full details in user-facing logs (bots don't get this info in GameState)
            cards_str = ', '.join(str(c) for c in top_three) if top_three else 'none'
            self._log(f"  → See the Future: {bot.name} sees [{cards_str}]")
            try:
                bot.see_the_future(self.game_state.copy(), top_three)
            except Exception as e:
                self._log(f"  ERROR: {bot.name} raised exception in see_the_future: {e}")
            return True
        elif card.card_type == CardType.SHUFFLE:
            # Check for Nope
            if self._check_for_nope(f"{bot.name} playing Shuffle", bot):
                return False
            self._log("  → Shuffle: Deck shuffled")
            self.deck.shuffle()
            return True
        elif card.card_type == CardType.ATTACK:
            # Check for Nope
            if self._check_for_nope(f"{bot.name} playing Attack", bot):
                return False
            # Attack: End current turn without drawing, give remaining turns + 2 to next player
            # If player has N turns left, next player gets (N-1) + 2 = N+1 turns
            self._log(f"  → Attack: Next player takes {self.turns_to_take + 1} turn(s)")
            self.turns_to_take = -(self.turns_to_take + 1)  # Negative signals Attack was played
            return True
        elif card.card_type == CardType.FAVOR:
            self._execute_favor(bot)
            return True
        elif card.card_type == CardType.NOPE:
            self._log("  → Nope can only be played in response to actions")
            return True
        # Cat cards have no effect when played alone
        return True
    
    def _execute_favor(self, bot: Bot) -> None:
        """Execute Favor card: target chooses what card to give."""
        alive_others = self._get_alive_bots_except(bot)
        if not alive_others:
            self._log(f"  → No targets available for Favor")
            return
        
        try:
            # Select target first
            target = bot.choose_target(self.game_state.copy(), alive_others, TargetContext.FAVOR)
            if not target:
                self._log(f"  → No target selected")
                return
            
            self._log(f"  → {bot.name} targets {target.name}")
            
            # Check for Nope with target information
            if self._check_for_nope(f"{bot.name} playing Favor on {target.name}", bot):
                return
            
            if not target.hand:
                self._log(f"  → {target.name} has no cards")
                return
            
            # Target chooses which card to give
            card_to_give = target.choose_card_from_hand(self.game_state.copy())
            if card_to_give and target.has_card(card_to_give):
                target.remove_card(card_to_give)
                bot.add_card(card_to_give)
                # Show full details in user-facing logs (bots don't get this info in GameState)
                self._log(f"  → {target.name} gives {card_to_give} to {bot.name}")
                # Notify bots (they don't know which specific card)
                self._notify_all_bots(f"{target.name} gives a card to {bot.name}", bot)
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
            # Notify all bots about the Exploding Kitten draw
            self._notify_all_bots(f"{bot.name} drew an Exploding Kitten", bot)
            self._handle_exploding_kitten(bot, drawn_card)
        else:
            self._log(f"  → Drew: {drawn_card}")
            bot.add_card(drawn_card)
            # Notify all bots about the draw (but not which card)
            self._notify_all_bots(f"{bot.name} draws a card", bot)

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
                # Notify all bots about the defuse
                self._notify_all_bots(f"{bot.name} defused an Exploding Kitten", bot)
                self.game_state.was_last_card_exploding_kitten = True
            except Exception as e:
                self._log(f"  ERROR: {bot.name} raised exception in handle_exploding_kitten: {e}")
                # Default: put it back on top
                self.deck.add_to_top(exploding_kitten)
                self._log(f"  → Defused! Exploding Kitten placed on top (default)")
                # Notify all bots about the defuse
                self._notify_all_bots(f"{bot.name} defused an Exploding Kitten", bot)
                self.game_state.was_last_card_exploding_kitten = True
        else:
            self._log(f"  💀 {bot.name} has no Defuse card and EXPLODES!")
            bot.alive = False
            self.game_state.alive_bots -= 1
            # Notify all bots about the elimination
            self._notify_all_bots(f"{bot.name} exploded and is eliminated", bot)
            self.game_state.history_of_played_cards.append(exploding_kitten)
            self.game_state.was_last_card_exploding_kitten = False
