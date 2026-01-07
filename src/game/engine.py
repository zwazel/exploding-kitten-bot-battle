"""
Main game engine orchestrator.

The GameEngine is the central controller that manages the game flow,
coordinates bots, handles card plays, and records all events.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from game.bots.base import (
    Action,
    Bot,
    DefuseAction,
    DrawCardAction,
    GiveCardAction,
    PassAction,
    PlayCardAction,
    PlayComboAction,
)
from game.bots.loader import BotLoader
from game.bots.view import BotView
from game.cards.base import Card
from game.cards import register_all_cards
from game.cards.registry import CardRegistry
from game.history import EventType, GameEvent, GameHistory
from game.rng import DeterministicRNG
from game.state import GameState
from game.turns import ReactionRound, RoundPhase, TurnManager


class GameEngine:
    """
    The main game engine that orchestrates the entire game.
    
    Responsibilities:
    - Managing game state (protected from bots)
    - Loading and coordinating bots
    - Handling card plays and reactions
    - Recording all events for replay
    - Enforcing game rules
    """
    
    def __init__(self, seed: int = 42) -> None:
        """
        Initialize the game engine.
        
        Args:
            seed: Seed for deterministic randomness.
        """
        self._rng: DeterministicRNG = DeterministicRNG(seed)
        self._state: GameState = GameState()
        self._history: GameHistory = GameHistory()
        self._turn_manager: TurnManager = TurnManager()
        self._registry: CardRegistry = CardRegistry()
        self._bots: dict[str, Bot] = {}
        self._bot_loader: BotLoader = BotLoader()
        self._game_running: bool = False
        
        # Register all game cards
        register_all_cards(self._registry)
    
    @property
    def rng(self) -> DeterministicRNG:
        """Get the deterministic RNG."""
        return self._rng
    
    @property
    def history(self) -> GameHistory:
        """Get the game history."""
        return self._history
    
    @property
    def registry(self) -> CardRegistry:
        """Get the card registry."""
        return self._registry
    
    @property
    def is_running(self) -> bool:
        """Check if the game is currently running."""
        return self._game_running
    
    # --- Bot Management ---
    
    def add_bot(self, bot: Bot) -> None:
        """
        Add a bot to the game.
        
        Args:
            bot: The bot to add.
        """
        base_name: str = bot.name
        player_id: str = base_name
        
        # Generate unique player ID if name already exists
        counter: int = 1
        while player_id in self._bots:
            counter += 1
            player_id = f"{base_name}_{counter}"
        
        self._bots[player_id] = bot
        self._state.add_player(player_id)
        self._record_event(EventType.PLAYER_JOINED, player_id)
    
    def load_bots_from_directory(self, directory: str | Path) -> list[Bot]:
        """
        Load bots from a directory.
        
        Args:
            directory: Path to the bots directory.
            
        Returns:
            List of loaded bots.
        """
        bots: list[Bot] = self._bot_loader.load_from_directory(directory)
        for bot in bots:
            self.add_bot(bot)
        return bots
    
    # --- Deck Management ---
    
    def load_deck_from_config(self, config_path: str | Path) -> None:
        """
        Load the deck from a configuration file.
        
        Args:
            config_path: Path to the deck config JSON file.
        """
        deck: list[Card] = self._registry.create_deck_from_file(config_path)
        self._state._draw_pile = deck
    
    def create_deck(self, config: dict[str, int]) -> None:
        """
        Create a deck from a configuration dictionary.
        
        Args:
            config: Dictionary mapping card types to counts.
        """
        deck: list[Card] = self._registry.create_deck(config)
        self._state._draw_pile = deck
    
    def shuffle_deck(self) -> None:
        """Shuffle the draw pile."""
        self._rng.shuffle(self._state._draw_pile)
        self._record_event(EventType.DECK_SHUFFLED)
    
    # --- View Creation (Anti-Cheat) ---
    
    def _create_bot_view(self, player_id: str) -> BotView:
        """
        Create a safe view of the game state for a specific bot.
        
        This is the anti-cheat mechanism - bots can only see what
        they're allowed to see through this view.
        
        Args:
            player_id: The player to create the view for.
            
        Returns:
            A BotView with only allowed information.
        """
        player_state = self._state.get_player(player_id)
        current_player_id: str = self._state.current_player_id or ""
        
        # Get other players' card counts (not their actual cards!)
        other_player_counts: dict[str, int] = {}
        other_player_ids: list[str] = []
        for pid, pstate in self._state.players.items():
            if pid != player_id and pstate.is_alive:
                other_player_counts[pid] = len(pstate.hand)
                other_player_ids.append(pid)
        
        # Get recent events (last 10 for context)
        all_events: tuple[GameEvent, ...] = self._history.get_events()
        recent: tuple[GameEvent, ...] = all_events[-10:] if all_events else ()
        
        return BotView(
            my_id=player_id,
            my_hand=tuple(player_state.hand) if player_state else (),
            my_turns_remaining=self._turn_manager.get_turns_remaining(player_id),
            discard_pile=tuple(self._state.discard_pile),
            draw_pile_count=self._state.draw_pile_count,
            other_players=tuple(other_player_ids),
            other_player_card_counts=other_player_counts,
            current_player=current_player_id,
            turn_order=self._turn_manager.turn_order,
            is_my_turn=(player_id == current_player_id),
            recent_events=recent,
        )
    
    # --- Event Recording ---
    
    def _record_event(
        self,
        event_type: EventType,
        player_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> GameEvent:
        """Record an event and notify all bots."""
        event: GameEvent = self._history.record(event_type, player_id, data)
        
        # Notify all bots about the event
        for pid, bot in self._bots.items():
            if self._state.players.get(pid, None) is not None:
                view: BotView = self._create_bot_view(pid)
                bot.on_event(event, view)
        
        return event
    
    # --- Card Actions ---
    
    def draw_cards(self, player_id: str, count: int = 1) -> tuple[list[Card], bool]:
        """
        Draw cards from the draw pile.
        
        If an Exploding Kitten is drawn, handle the explosion/defuse flow.
        
        Args:
            player_id: The player drawing cards.
            count: Number of cards to draw.
            
        Returns:
            Tuple of (drawn cards, whether player exploded).
        """
        drawn: list[Card] = []
        player_state = self._state.get_player(player_id)
        
        for _ in range(count):
            card: Card | None = self._state.draw_card()
            if card is None or player_state is None:
                continue
            
            # Check if it's an Exploding Kitten
            if card.card_type == "ExplodingKittenCard":
                self._record_event(
                    EventType.EXPLODING_KITTEN_DRAWN,
                    player_id,
                )
                
                # Check for Defuse card
                exploded: bool = self._handle_explosion(player_id, card)
                if exploded:
                    return drawn, True
                # If defused, continue (kitten is reinserted, not added to hand)
            else:
                player_state.hand.append(card)
                drawn.append(card)
                self._record_event(
                    EventType.CARD_DRAWN,
                    player_id,
                    {"card_type": card.card_type},
                )
                self.log(f"{player_id} drew: {card.name}")
        
        return drawn, False
    
    def _handle_explosion(self, player_id: str, kitten: Card) -> bool:
        """
        Handle an Exploding Kitten draw.
        
        Args:
            player_id: The player who drew the kitten.
            kitten: The Exploding Kitten card.
            
        Returns:
            True if player exploded, False if defused.
        """
        player_state = self._state.get_player(player_id)
        bot: Bot | None = self._bots.get(player_id)
        
        if not player_state or not bot:
            return True
        
        # Look for Defuse card
        defuse_card: Card | None = None
        for card in player_state.hand:
            if card.card_type == "DefuseCard":
                defuse_card = card
                break
        
        if defuse_card is None:
            # No Defuse - player explodes!
            self.log(f"{player_id} drew an Exploding Kitten and has no Defuse!")
            self._eliminate_player(player_id)
            return True
        
        # Use Defuse card
        player_state.hand.remove(defuse_card)
        self._state.discard(defuse_card)
        
        self._record_event(
            EventType.EXPLODING_KITTEN_DEFUSED,
            player_id,
        )
        
        self.log(f"{player_id} defused the Exploding Kitten!")
        
        # Bot chooses where to reinsert the kitten
        view: BotView = self._create_bot_view(player_id)
        draw_pile_size: int = self._state.draw_pile_count
        insert_pos: int = bot.choose_defuse_position(view, draw_pile_size)
        
        # Clamp to valid range
        insert_pos = max(0, min(insert_pos, draw_pile_size))
        
        # Insert the kitten (secretly)
        self._state.insert_in_draw_pile(kitten, insert_pos)
        
        self._record_event(
            EventType.EXPLODING_KITTEN_INSERTED,
            player_id,
            {"position": "secret"},  # Don't reveal position
        )
        
        return False
    
    def _eliminate_player(self, player_id: str) -> None:
        """Eliminate a player from the game."""
        player_state = self._state.get_player(player_id)
        if player_state:
            # Move all cards to discard
            for card in player_state.hand:
                self._state.discard(card)
            player_state.hand.clear()
            player_state.is_alive = False
        
        self._turn_manager.remove_player(player_id)
        
        self._record_event(
            EventType.PLAYER_ELIMINATED,
            player_id,
        )
        
        self.log(f"{player_id} has been eliminated!")
    
    def peek_draw_pile(self, player_id: str, count: int = 3) -> tuple[Card, ...]:
        """
        Let a player peek at the top cards of the draw pile.
        
        Args:
            player_id: The player peeking.
            count: Number of cards to peek at.
            
        Returns:
            Tuple of cards in draw order (first = next to draw).
        """
        draw_pile: list[Card] = self._state.draw_pile
        actual_count: int = min(count, len(draw_pile))
        
        # Index 0 is the top (next card to draw)
        peeked: tuple[Card, ...] = tuple(draw_pile[:actual_count]) if actual_count > 0 else ()
        
        # Record what was actually seen for replay
        self._record_event(
            EventType.CARDS_PEEKED,
            player_id,
            {
                "count": actual_count,
                "card_types": [c.card_type for c in peeked],
            },
        )
        
        return peeked
    
    def request_favor(self, requester_id: str, target_id: str) -> Card | None:
        """
        Request a favor from another player.
        
        The target player must give one card of their choice.
        
        Args:
            requester_id: Player requesting the favor.
            target_id: Player who must give a card.
            
        Returns:
            The card given, or None if target has no cards.
        """
        target_state = self._state.get_player(target_id)
        requester_state = self._state.get_player(requester_id)
        target_bot: Bot | None = self._bots.get(target_id)
        
        if not target_state or not target_state.hand or not requester_state or not target_bot:
            return None
        
        self._record_event(
            EventType.FAVOR_REQUESTED,
            requester_id,
            {"target": target_id},
        )
        
        # Target chooses which card to give
        target_view: BotView = self._create_bot_view(target_id)
        card_to_give: Card = target_bot.choose_card_to_give(target_view, requester_id)
        
        # Validate the card is in their hand
        if card_to_give not in target_state.hand:
            # If invalid choice, give a random card
            card_to_give = target_state.hand[0]
        
        target_state.hand.remove(card_to_give)
        requester_state.hand.append(card_to_give)
        
        self._record_event(
            EventType.CARD_GIVEN,
            target_id,
            {"to": requester_id, "card_type": card_to_give.card_type},
        )
        
        self.log(f"{target_id} gave {card_to_give.name} to {requester_id}")
        
        return card_to_give
    
    def skip_turn(self, player_id: str) -> None:
        """Skip the current turn (consume without drawing)."""
        self._turn_manager.skip_turn(player_id)
        self._record_event(EventType.TURN_SKIPPED, player_id)
    
    def attack_next_player(self, player_id: str, extra_turns: int) -> None:
        """
        End current player's turn and give next player extra turns.
        
        Args:
            player_id: The attacking player.
            extra_turns: Number of turns to add to next player.
        """
        alive_players: list[str] = self._state.get_alive_players()
        next_player: str | None = self._turn_manager.advance_to_next_player(
            alive_players
        )
        
        if next_player:
            self._turn_manager.add_turns(next_player, extra_turns - 1)
            self._record_event(
                EventType.TURNS_ADDED,
                next_player,
                {"extra_turns": extra_turns, "attacker": player_id},
            )
    
    def steal_random_card(self, player_id: str, target_id: str | None = None) -> Card | None:
        """
        Steal a random card from another player.
        
        Args:
            player_id: The player stealing.
            target_id: Specific target, or None for random target.
            
        Returns:
            The stolen card, or None if no cards to steal.
        """
        if target_id is None:
            other_players: list[str] = [
                pid for pid in self._state.get_alive_players()
                if pid != player_id
            ]
            if not other_players:
                return None
            target_id = self._rng.choice(other_players)
        
        target_state = self._state.get_player(target_id)
        player_state = self._state.get_player(player_id)
        
        if not target_state or not target_state.hand or not player_state:
            return None
        
        stolen_card: Card = self._rng.choice(target_state.hand)
        target_state.hand.remove(stolen_card)
        player_state.hand.append(stolen_card)
        
        self._record_event(
            EventType.CARD_STOLEN,
            player_id,
            {"target": target_id, "card_type": stolen_card.card_type},
        )
        
        self.log(f"{player_id} stole {stolen_card.name} from {target_id}")
        
        return stolen_card
    
    def log(self, message: str) -> None:
        """Log a message to the console."""
        print(f"[Game] {message}")
    
    def shuffle_deck(self) -> None:
        """Shuffle the draw pile."""
        self._rng.shuffle(self._state.draw_pile)
        self._record_event(EventType.DECK_SHUFFLED)
    
    # --- Reaction System ---
    
    def _run_reaction_round(self, triggering_event: GameEvent) -> bool:
        """
        Run a reaction round where players can respond to an action.
        
        Args:
            triggering_event: The event that triggered reactions.
            
        Returns:
            True if the action was negated, False if it proceeds.
        """
        current_player: str | None = self._state.current_player_id
        if not current_player:
            return False
        
        alive_players: list[str] = self._state.get_alive_players()
        reaction_round: ReactionRound = self._turn_manager.start_reaction_round(
            triggering_event,
            current_player,
            alive_players,
        )
        
        self._record_event(
            EventType.REACTION_ROUND_START,
            data={"triggering_event_step": triggering_event.step},
        )
        
        nope_count: int = 0
        
        while reaction_round.pending_players:
            reactor_id: str = reaction_round.pending_players.pop(0)
            bot: Bot | None = self._bots.get(reactor_id)
            
            if not bot:
                continue
            
            view: BotView = self._create_bot_view(reactor_id)
            action: Action | None = bot.react(view, triggering_event)
            
            if action is None or isinstance(action, PassAction):
                self._record_event(
                    EventType.REACTION_SKIPPED,
                    reactor_id,
                )
                continue
            
            if isinstance(action, PlayCardAction):
                card: Card = action.card
                
                if not card.can_play_as_reaction():
                    self._record_event(
                        EventType.REACTION_SKIPPED,
                        reactor_id,
                        {"reason": "card_not_reaction"},
                    )
                    continue
                
                # Remove card from player's hand
                player_state = self._state.get_player(reactor_id)
                if player_state and card in player_state.hand:
                    player_state.hand.remove(card)
                    self._state.discard(card)
                    
                    reaction_event: GameEvent = self._record_event(
                        EventType.REACTION_PLAYED,
                        reactor_id,
                        {"card_type": card.card_type},
                    )
                    
                    card.execute(self, reactor_id)
                    nope_count += 1
                    
                    # Start a new nested reaction round for this reaction
                    # This allows counter-nopes
                    if self._run_reaction_round(reaction_event):
                        # The reaction was negated
                        nope_count -= 1
        
        self._turn_manager.end_reaction_round()
        self._record_event(EventType.REACTION_ROUND_END)
        
        # Odd number of nopes = action negated
        return nope_count % 2 == 1
    
    def _play_card(
        self,
        player_id: str,
        card: Card,
        target_player_id: str | None = None,
    ) -> bool:
        """
        Play a single card.
        
        Args:
            player_id: The player playing the card.
            card: The card to play.
            target_player_id: Target player for targeted cards (Favor, etc.)
            
        Returns:
            True if the card effect was executed, False if negated.
        """
        player_state = self._state.get_player(player_id)
        if not player_state or card not in player_state.hand:
            return False
        
        # Remove and discard the card
        player_state.hand.remove(card)
        self._state.discard(card)
        
        # Record the play with full details for replay
        event_data: dict[str, Any] = {"card_type": card.card_type}
        if target_player_id:
            event_data["target"] = target_player_id
        
        play_event: GameEvent = self._record_event(
            EventType.CARD_PLAYED,
            player_id,
            event_data,
        )
        
        # Check if the card can be reacted to (reaction cards like Nope)
        if not card.can_play_as_reaction():
            # Run reaction round
            if self._run_reaction_round(play_event):
                self.log(f"{player_id}'s {card.name} was negated!")
                return False
        
        # Execute the card effect
        card.execute(self, player_id)
        return True
    
    def _play_combo(
        self,
        player_id: str,
        cards: list[Card],
        target_player_id: str | None = None,
    ) -> bool:
        """
        Play a combo of cards.
        
        Combo patterns:
        - 2 of a kind: steal random card from target player
        - 3 of a kind: name and steal specific card (placeholder: random)
        - 5 different card types: draw a card from the discard pile
        
        Args:
            player_id: The player playing the combo.
            cards: The cards in the combo.
            target_player_id: Target for steal combos.
            
        Returns:
            True if the combo was executed, False if invalid or negated.
        """
        player_state = self._state.get_player(player_id)
        if not player_state:
            return False
        
        # Verify all cards are in hand and can combo
        for card in cards:
            if card not in player_state.hand:
                return False
            if not card.can_combo():
                return False
        
        # Determine combo type
        card_types: list[str] = [c.card_type for c in cards]
        unique_types: set[str] = set(card_types)
        
        combo_type: str
        if len(cards) == 5 and len(unique_types) == 5:
            combo_type = "five_different"
        elif len(unique_types) == 1 and len(cards) >= 2:
            if len(cards) >= 3:
                combo_type = "three_of_a_kind"
            else:
                combo_type = "two_of_a_kind"
        else:
            self.log(f"{player_id} tried invalid combo: {card_types}")
            return False
        
        # Remove and discard all cards
        for card in cards:
            player_state.hand.remove(card)
            self._state.discard(card)
        
        # Record the combo
        combo_event: GameEvent = self._record_event(
            EventType.COMBO_PLAYED,
            player_id,
            {
                "card_types": card_types,
                "count": len(cards),
                "combo_type": combo_type,
                "target": target_player_id,
            },
        )
        
        # Run reaction round
        if self._run_reaction_round(combo_event):
            self.log(f"{player_id}'s combo was negated!")
            return False
        
        # Execute combo effect based on pattern
        self._execute_combo_effect(player_id, combo_type, target_player_id)
        
        return True
    
    def _execute_combo_effect(
        self,
        player_id: str,
        combo_type: str,
        target_player_id: str | None,
    ) -> None:
        """
        Execute the effect of a combo based on its type.
        
        Args:
            player_id: The player who played the combo.
            combo_type: The type of combo (two_of_a_kind, three_of_a_kind, five_different).
            target_player_id: Target player for steal combos.
        """
        if combo_type == "two_of_a_kind":
            # Steal a random card from target player
            if target_player_id:
                self._steal_card_from_player(player_id, target_player_id)
            else:
                self.steal_random_card(player_id)
            self.log(f"{player_id} played 2-of-a-kind and stole a card!")
        
        elif combo_type == "three_of_a_kind":
            # In the real game, player names a card to steal
            # For placeholder, just steal a random card from target
            if target_player_id:
                self._steal_card_from_player(player_id, target_player_id)
            else:
                self.steal_random_card(player_id)
            self.log(f"{player_id} played 3-of-a-kind and stole a specific card!")
        
        elif combo_type == "five_different":
            # Draw a card from the discard pile
            self._draw_from_discard(player_id)
            self.log(f"{player_id} played 5-different and drew from discard!")
    
    def _steal_card_from_player(
        self,
        thief_id: str,
        target_id: str,
    ) -> Card | None:
        """
        Steal a random card from a specific player.
        
        Args:
            thief_id: Player stealing.
            target_id: Player being stolen from.
            
        Returns:
            The stolen card, or None.
        """
        target_state = self._state.get_player(target_id)
        thief_state = self._state.get_player(thief_id)
        
        if not target_state or not target_state.hand or not thief_state:
            return None
        
        stolen_card: Card = self._rng.choice(target_state.hand)
        target_state.hand.remove(stolen_card)
        thief_state.hand.append(stolen_card)
        
        self._record_event(
            EventType.CARD_PLAYED,
            thief_id,
            {"action": "steal", "target": target_id, "card_type": stolen_card.card_type},
        )
        
        return stolen_card
    
    def _draw_from_discard(self, player_id: str) -> Card | None:
        """
        Let a player draw a card from the discard pile.
        
        For placeholder, draws the top card. Real implementation would
        let the player choose.
        
        Args:
            player_id: The player drawing.
            
        Returns:
            The drawn card, or None if discard is empty.
        """
        player_state = self._state.get_player(player_id)
        
        if not self._state.discard_pile or not player_state:
            return None
        
        # For placeholder, take the top card
        card: Card = self._state.discard_pile.pop()
        player_state.hand.append(card)
        
        self._record_event(
            EventType.CARD_DRAWN,
            player_id,
            {"card_type": card.card_type, "from": "discard"},
        )
        
        return card
    
    # --- Game Flow ---
    
    def setup_game(self, initial_hand_size: int = 7) -> None:
        """
        Set up the game for play.
        
        Per Exploding Kittens rules:
        1. Remove Exploding Kittens and Defuse cards from deck
        2. Deal initial hands from the remaining cards
        3. Give each player 1 Defuse card
        4. Shuffle remaining Defuse cards and (num_players - 1) Exploding Kittens back into deck
        
        Note: Exploding Kittens are always (num_players - 1), generated at runtime.
        Defuse cards must be at least (num_players + 1).
        
        Args:
            initial_hand_size: Number of cards to deal to each player.
        """
        self.log("=== SETUP PHASE ===")
        
        player_ids: list[str] = list(self._bots.keys())
        num_players = len(player_ids)
        
        # Remove any Exploding Kittens and Defuse cards from deck (we'll add the right amounts)
        defuse_cards: list[Card] = []
        remaining_cards: list[Card] = []
        
        for card in self._state._draw_pile:
            if card.card_type == "ExplodingKittenCard":
                # Ignore - we generate the correct amount
                pass
            elif card.card_type == "DefuseCard":
                defuse_cards.append(card)
            else:
                remaining_cards.append(card)
        
        # Validate Defuse card count: must be at least (num_players + 1)
        min_defuse = num_players + 1
        if len(defuse_cards) < min_defuse:
            self.log(f"WARNING: Config has {len(defuse_cards)} Defuse cards, need at least {min_defuse}. Adding extra Defuse cards.")
            # Add missing Defuse cards
            from game.cards.exploding_kitten import DefuseCard
            while len(defuse_cards) < min_defuse:
                defuse_cards.append(DefuseCard())
        
        # Generate exactly (num_players - 1) Exploding Kittens
        num_kittens = num_players - 1
        from game.cards.exploding_kitten import ExplodingKittenCard
        exploding_kittens: list[Card] = [ExplodingKittenCard() for _ in range(num_kittens)]
        
        # Set up the draw pile without Exploding Kittens and Defuse
        self._state._draw_pile = remaining_cards
        
        # Shuffle the safe deck
        self.shuffle_deck()
        
        # Set up turn order (randomized)
        self._rng.shuffle(player_ids)
        self._state._turn_order = player_ids
        self._state._current_player_index = 0
        self._turn_manager.setup(player_ids)
        
        # Deal initial hands (safe - no explosions possible)
        self.log("Dealing initial hands...")
        for player_id in player_ids:
            self.draw_cards(player_id, initial_hand_size)
        
        # Give each player 1 Defuse card (per official rules)
        for player_id in player_ids:
            if defuse_cards:
                defuse = defuse_cards.pop(0)
                player_state = self._state.get_player(player_id)
                if player_state:
                    player_state.hand.append(defuse)
        
        # Add remaining Defuse cards back to deck
        for card in defuse_cards:
            self._state._draw_pile.append(card)
        
        # Add all Exploding Kittens to deck
        for card in exploding_kittens:
            self._state._draw_pile.append(card)
        
        # Shuffle the deck with Exploding Kittens now included
        self.shuffle_deck()
        
        self.log(f"Setup complete. {num_players} players, {num_kittens} Exploding Kittens in deck.")
        self.log("=== GAME START ===")
        
        self._record_event(
            EventType.GAME_START,
            data={"turn_order": player_ids, "hand_size": initial_hand_size},
        )
    
    def _run_turn(self, player_id: str) -> None:
        """Run a single turn for a player."""
        bot: Bot | None = self._bots.get(player_id)
        if not bot:
            return
        
        turns_remaining: int = self._turn_manager.get_turns_remaining(player_id)
        if turns_remaining > 1:
            self.log(f"--- {player_id}'s turn ({turns_remaining} turns remaining) ---")
        else:
            self.log(f"--- {player_id}'s turn ---")
        
        self._record_event(EventType.TURN_START, player_id)
        
        while True:
            view: BotView = self._create_bot_view(player_id)
            action: Action = bot.take_turn(view)
            
            if isinstance(action, DrawCardAction):
                # End turn by drawing a card
                _, exploded = self.draw_cards(player_id, 1)
                if exploded:
                    # Player was eliminated, exit turn
                    return
                break
            
            elif isinstance(action, PlayCardAction):
                card: Card = action.card
                if card.can_play(view, is_own_turn=True):
                    self._play_card(player_id, card, action.target_player_id)
                    
                    # Card signals if it ends the turn (Skip/Attack)
                    if card.ends_turn():
                        has_more: bool = self._turn_manager.get_turns_remaining(player_id) > 0
                        self._record_event(
                            EventType.TURN_END,
                            player_id,
                            {"has_more_turns": has_more},
                        )
                        return
                else:
                    self.log(f"{player_id} tried to play {card.name} but it's not allowed")
            
            elif isinstance(action, PlayComboAction):
                cards: list[Card] = list(action.cards)
                if len(cards) >= 2 and all(c.can_combo() for c in cards):
                    self._play_combo(player_id, cards, action.target_player_id)
                else:
                    self.log(f"{player_id} tried to play invalid combo")
            
            elif isinstance(action, PassAction):
                # Pass without doing anything - still need to draw to end turn
                continue
        
        # Consume the turn (for draw actions)
        has_more_turns: bool = self._turn_manager.consume_turn(player_id)
        
        self._record_event(
            EventType.TURN_END,
            player_id,
            {"has_more_turns": has_more_turns},
        )

    
    def run(self, history_file: str | Path | None = None) -> str | None:
        """
        Run the game to completion.
        
        Args:
            history_file: Optional path to save game history JSON.
        
        Returns:
            The winner's player ID, or None if no winner.
        """
        if len(self._bots) < 2:
            self.log("Need at least 2 bots to play!")
            return None
        
        self._game_running = True
        self.setup_game()
        
        # Main game loop
        while self._game_running:
            alive_players: list[str] = self._state.get_alive_players()
            
            if len(alive_players) <= 1:
                # Game over
                winner: str | None = alive_players[0] if alive_players else None
                self._game_running = False
                self._record_event(
                    EventType.GAME_END,
                    winner,
                    {"winner": winner},
                )
                self.log(f"Game Over! Winner: {winner}")
                
                # Save history if requested
                if history_file:
                    self.save_history(history_file)
                    self.log(f"History saved to {history_file}")
                
                return winner
            
            current_player_id: str | None = self._turn_manager.current_player_id
            if not current_player_id or current_player_id not in alive_players:
                self._turn_manager.advance_to_next_player(alive_players)
                current_player_id = self._turn_manager.current_player_id
            
            if current_player_id:
                self._run_turn(current_player_id)
                
                # Move to next player if current player is done
                if self._turn_manager.get_turns_remaining(current_player_id) == 0:
                    self._turn_manager.advance_to_next_player(alive_players)
        
        return None
    
    def save_history(self, file_path: str | Path) -> None:
        """Save the game history to a JSON file."""
        path: Path = Path(file_path)
        with path.open("w", encoding="utf-8") as f:
            f.write(self._history.to_json())
