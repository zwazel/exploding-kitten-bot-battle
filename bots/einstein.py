"""
==============================================================================
EINSTEIN BOT v3 - The Probability Mastermind
==============================================================================

Einstein uses probability calculations and strategic reasoning to dominate.

Core Strategy:
1. Calculate explosion probability to make informed decisions
2. Defensive: Nope any hurtful actions against himself
3. Evasive: Use Attack > Skip > Shuffle when danger is known (prefer Attack)
4. After Shuffle, consider risk lower (deck is randomized)
5. Combo Priority:
   a. 5-different: ONLY if we KNOW FOR SURE there's a Defuse in discard
   b. 3-of-a-kind: Target player who should have Defuse, name "DefuseCard"
   c. 2-of-a-kind: Target player likely with Defuse, random steal
   d. Favor: As backup to get good cards
6. Strategic defuse placement to maximize opponent elimination
"""

from game.bots.base import (
    Action,
    Bot,
    DrawCardAction,
    PlayCardAction,
    PlayComboAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.history import GameEvent, EventType


class Einstein(Bot):
    """
    A probability-focused bot that calculates risk and plays strategically.
    
    Core Philosophy:
    - Calculate explosion probability for every decision
    - Defend against all hurtful actions with Nope
    - Prioritize Attack over Skip over Shuffle for evasion
    - Use combos strategically to steal Defuse cards
    """
    
    def __init__(self) -> None:
        """Initialize Einstein with state tracking."""
        # Track top cards from See the Future
        self._known_top_cards: list[str] = []
        
        # Track draws since last peek
        self._cards_drawn_since_peek: int = 0
        
        # Track if deck was shuffled since peek
        self._deck_shuffled_since_peek: bool = False
        
        # When True, we just shuffled - risk is "reset"
        self._just_shuffled: bool = False
        
        # Track initial player count for kitten calculations
        self._initial_player_count: int | None = None
        
        # Track eliminated players
        self._eliminated_count: int = 0
        
        # Track who has used Defuse (they likely don't have another)
        self._players_who_defused: set[str] = set()
        
        # Track players who we KNOW have Defuse (not used yet)
        # At start, everyone has one Defuse
        self._players_with_defuse: set[str] = set()
        
        # Track if Defuse is in discard pile
        self._defuse_in_discard: bool = False
        
        # Einstein personality quotes
        self._smart_quotes: list[str] = [
            "E = mc²",
            "Probability favors the prepared.",
            "The math is never wrong.",
            "Calculating optimal strategy...",
        ]
        
        self._danger_quotes: list[str] = [
            "Evasive maneuvers!",
            "The probability is... unfavorable!",
            "Strategic retreat required!",
        ]
        
        self._attack_quotes: list[str] = [
            "Your problem now!",
            "Taste my probability!",
            "Passing the equation!",
        ]
        
        self._skip_quotes: list[str] = [
            "Skipping to safety!",
            "The math says: skip!",
            "Not today, kitten!",
        ]
        
        self._shuffle_quotes: list[str] = [
            "Reshuffling the probabilities!",
            "Randomizing the universe!",
            "Chaos theory in action!",
        ]
        
        self._steal_quotes: list[str] = [
            "I require your Defuse!",
            "For science!",
            "Your cards are now my cards!",
        ]
        
        self._defuse_quotes: list[str] = [
            "Elementary.",
            "As my calculations predicted.",
            "Probability of survival: 100%",
        ]
        
        self._nope_quotes: list[str] = [
            "Hypothesis rejected!",
            "Your theory is flawed!",
            "NOPE! Not on my watch!",
        ]
        
        self._death_quotes: list[str] = [
            "Even geniuses err...",
            "The probability was... wrong?",
            "Impossible!",
        ]

    @property
    def name(self) -> str:
        """Return the bot's name."""
        return "Einstein"
    
    # =========================================================================
    # PROBABILITY CALCULATIONS
    # =========================================================================
    
    def _calc_explosion_probability(self, view: BotView) -> float:
        """
        Calculate probability of drawing an Exploding Kitten.
        
        P(explosion) = kittens_in_deck / draw_pile_size
        
        If we just shuffled, we consider risk "reset" to base probability.
        
        Returns: Probability from 0.0 to 1.0
        """
        draw_pile_size = view.draw_pile_count
        if draw_pile_size == 0:
            return 0.0
        
        kittens = self._estimate_kittens(view)
        base_prob = kittens / draw_pile_size
        
        # After shuffle, we don't have any intel - just use base probability
        # This is logically correct, but we treat it as slightly lower
        # because the danger isn't "concentrated" at top
        if self._just_shuffled:
            return base_prob  # No adjustment needed, but no known danger
        
        return base_prob
    
    def _estimate_kittens(self, view: BotView) -> int:
        """
        Estimate kittens remaining in deck.
        
        Initial = players - 1
        Each elimination removes one kitten (usually exploded).
        """
        if self._initial_player_count is None:
            total = len(view.other_players) + 1
            return max(0, total - 1)
        
        initial_kittens = self._initial_player_count - 1
        return max(0, initial_kittens - self._eliminated_count)
    
    def _is_top_dangerous(self) -> bool:
        """Check if we KNOW the top card is an Exploding Kitten."""
        if self._deck_shuffled_since_peek or not self._known_top_cards:
            return False
        
        idx = self._cards_drawn_since_peek
        if idx < len(self._known_top_cards):
            return self._known_top_cards[idx] == "ExplodingKittenCard"
        return False
    
    def _safe_draws_known(self) -> int:
        """How many draws are we CERTAIN are safe?"""
        if self._deck_shuffled_since_peek or not self._known_top_cards:
            return 0
        
        safe = 0
        for i in range(self._cards_drawn_since_peek, len(self._known_top_cards)):
            if self._known_top_cards[i] == "ExplodingKittenCard":
                break
            safe += 1
        return safe
    
    # =========================================================================
    # PLAYER ANALYSIS
    # =========================================================================
    
    def _get_players_with_likely_defuse(self, view: BotView) -> list[str]:
        """
        Get players who LIKELY have a Defuse card.
        
        A player likely has Defuse if:
        - They haven't used one yet
        - They have more cards (more chances)
        
        Returns: List of player IDs sorted by likelihood (highest first)
        """
        likely: list[tuple[str, float]] = []
        
        for player in view.other_players:
            if player in self._players_who_defused:
                # They used their Defuse, probably don't have another
                score = 0.1
            elif player in self._players_with_defuse:
                # We know they started with one and haven't used it
                score = 1.0
            else:
                # Unknown - estimate based on card count
                card_count = view.other_player_card_counts.get(player, 0)
                score = 0.5 + (card_count * 0.05)
            
            likely.append((player, score))
        
        # Sort by score descending
        likely.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in likely]
    
    def _get_weakest_opponent(self, view: BotView) -> str | None:
        """Find opponent with fewest cards (least options)."""
        if not view.other_players:
            return None
        return min(
            view.other_players,
            key=lambda p: view.other_player_card_counts.get(p, 0)
        )
    
    def _get_strongest_opponent(self, view: BotView) -> str | None:
        """Find opponent with most cards (biggest threat)."""
        if not view.other_players:
            return None
        return max(
            view.other_players,
            key=lambda p: view.other_player_card_counts.get(p, 0)
        )
    
    def _get_next_player(self, view: BotView) -> str | None:
        """Get the next player in turn order."""
        if not view.other_players:
            return None
        
        turn_order = list(view.turn_order)
        if view.my_id not in turn_order:
            return view.other_players[0]
        
        my_idx = turn_order.index(view.my_id)
        alive = set(view.other_players) | {view.my_id}
        
        for i in range(1, len(turn_order)):
            candidate = turn_order[(my_idx + i) % len(turn_order)]
            if candidate in alive and candidate != view.my_id:
                return candidate
        
        return view.other_players[0]
    
    def _get_next_player_after(self, player_id: str, view: BotView) -> str | None:
        """Get next player after a specific player."""
        turn_order = list(view.turn_order)
        if player_id not in turn_order:
            return None
        
        idx = turn_order.index(player_id)
        alive = set(view.other_players) | {view.my_id}
        
        for i in range(1, len(turn_order)):
            candidate = turn_order[(idx + i) % len(turn_order)]
            if candidate in alive:
                return candidate
        return None
    
    # =========================================================================
    # COMBO STRATEGIES
    # =========================================================================
    
    def _can_play_five_different(self, view: BotView) -> tuple[Card, ...] | None:
        """
        Check if we can play a 5-different combo.
        
        ONLY returns cards if we KNOW FOR SURE there's a Defuse in discard.
        
        Returns: Tuple of 5 cards, or None
        """
        # First check: Is there a Defuse in the discard pile?
        if not self._defuse_in_discard:
            return None
        
        # Verify by checking actual discard pile
        has_defuse = any(c.card_type == "DefuseCard" for c in view.discard_pile)
        if not has_defuse:
            return None
        
        # Group combo-eligible cards by type
        by_type: dict[str, list[Card]] = {}
        for card in view.my_hand:
            if card.can_combo():
                by_type.setdefault(card.card_type, []).append(card)
        
        if len(by_type) < 5:
            return None
        
        # Build the 5 different cards
        five_cards: list[Card] = []
        for card_type in list(by_type.keys())[:5]:
            five_cards.append(by_type[card_type][0])
        
        return tuple(five_cards)
    
    def _can_play_three_of_kind(self, view: BotView) -> tuple[tuple[Card, ...], str] | None:
        """
        Check if we can play 3-of-a-kind to steal Defuse.
        
        Target: Player who should have a Defuse for sure.
        
        Returns: (cards, target_id) or None
        """
        # Group combo-eligible cards by type
        by_type: dict[str, list[Card]] = {}
        for card in view.my_hand:
            if card.can_combo():
                by_type.setdefault(card.card_type, []).append(card)
        
        # Find a type with 3+ cards
        three_cards: tuple[Card, ...] | None = None
        for cards in by_type.values():
            if len(cards) >= 3:
                three_cards = tuple(cards[:3])
                break
        
        if three_cards is None:
            return None
        
        # Find target who likely has Defuse
        likely_defuse = self._get_players_with_likely_defuse(view)
        if not likely_defuse:
            return None
        
        # Target the one most likely to have Defuse
        return (three_cards, likely_defuse[0])
    
    def _can_play_two_of_kind(self, view: BotView) -> tuple[tuple[Card, ...], str] | None:
        """
        Check if we can play 2-of-a-kind to random steal.
        
        Target: Player who likely still has Defuse.
        
        Returns: (cards, target_id) or None
        """
        # Group combo-eligible cards by type
        by_type: dict[str, list[Card]] = {}
        for card in view.my_hand:
            if card.can_combo():
                by_type.setdefault(card.card_type, []).append(card)
        
        # Find a type with 2+ cards
        two_cards: tuple[Card, ...] | None = None
        for cards in by_type.values():
            if len(cards) >= 2:
                two_cards = tuple(cards[:2])
                break
        
        if two_cards is None:
            return None
        
        # Target player who likely has Defuse
        likely_defuse = self._get_players_with_likely_defuse(view)
        if not likely_defuse:
            # Target strongest opponent if no one likely has Defuse
            target = self._get_strongest_opponent(view)
            if target:
                return (two_cards, target)
            return None
        
        return (two_cards, likely_defuse[0])
    
    # =========================================================================
    # NOPE LOGIC (DEFENSIVE)
    # =========================================================================
    
    def _is_targeting_me(self, event: GameEvent, view: BotView) -> bool:
        """Check if an action is targeting this bot."""
        # Direct target
        if event.data.get("target_player_id") == view.my_id:
            return True
        if event.data.get("target") == view.my_id:
            return True
        
        # Attack targets next player
        card_type = event.data.get("card_type")
        if card_type == "AttackCard":
            attacker = event.player_id
            if attacker:
                next_p = self._get_next_player_after(attacker, view)
                if next_p == view.my_id:
                    return True
        
        return False
    
    def _is_hurtful_to_me(self, event: GameEvent, view: BotView) -> bool:
        """
        Check if this event is hurtful to Einstein.
        
        Hurtful events:
        - Attack targeting me
        - Favor targeting me
        - Combo steal targeting me
        """
        card_type = event.data.get("card_type")
        combo_type = event.data.get("combo_type")
        
        # Attack me
        if card_type == "AttackCard" and self._is_targeting_me(event, view):
            return True
        
        # Favor me
        if card_type == "FavorCard" and self._is_targeting_me(event, view):
            return True
        
        # Combo steal me
        if combo_type in ("two_of_a_kind", "three_of_a_kind"):
            if self._is_targeting_me(event, view):
                return True
        
        return False
    
    def _should_nope(self, event: GameEvent, view: BotView) -> bool:
        """
        Decide if we should nope this event.
        
        Einstein:
        1. ALWAYS nopes hurtful actions against himself
        2. Nopes opponents' See the Future when we have 2+ Nopes
        3. Nopes opponents' Shuffle when we know safe draws
        """
        # Always protect ourselves
        if self._is_hurtful_to_me(event, view):
            return True
        
        # Strategic noping with spare Nopes
        nope_count = view.count_cards_of_type("NopeCard")
        if nope_count >= 2:
            card_type = event.data.get("card_type")
            
            # Nope See the Future by opponents (deny them intel)
            if card_type == "SeeTheFutureCard" and event.player_id != view.my_id:
                return True
            
            # Nope Shuffle when we know safe draws (preserve our knowledge)
            if card_type == "ShuffleCard" and self._safe_draws_known() > 0:
                return True
        
        return False
    
    # =========================================================================
    # MAIN TURN LOGIC
    # =========================================================================
    
    def take_turn(self, view: BotView) -> Action:
        """
        Einstein's turn strategy:
        
        1. DANGER KNOWN: If top is exploding kitten, use Attack > Skip > Shuffle
        2. INTEL GATHERING: Use See-the-Future if we don't know what's coming
        3. COMBO PRIORITY: 5-diff (if Defuse in discard) > 3-of-kind > 2-of-kind > Favor
        4. HIGH PROBABILITY: Use evasion cards if explosion prob > threshold
        5. DRAW: If safe enough
        """
        import random
        
        explosion_prob = self._calc_explosion_probability(view)
        known_danger = self._is_top_dangerous()
        has_defuse = view.has_card_type("DefuseCard")
        safe_draws = self._safe_draws_known()
        
        # Reset "just shuffled" flag at start of decision
        self._just_shuffled = False
        
        # =====================================================================
        # PHASE 1: KNOWN DANGER - Use Attack > Skip > Shuffle
        # =====================================================================
        
        if known_danger:
            view.say(random.choice(self._danger_quotes))
            
            # PREFER ATTACK - passes the problem to next player
            attacks = view.get_cards_of_type("AttackCard")
            if attacks and view.other_players:
                view.say(random.choice(self._attack_quotes))
                return PlayCardAction(card=attacks[0])
            
            # SECOND: Skip - avoids drawing
            skips = view.get_cards_of_type("SkipCard")
            if skips:
                view.say(random.choice(self._skip_quotes))
                return PlayCardAction(card=skips[0])
            
            # THIRD: Shuffle - rerolls the danger
            shuffles = view.get_cards_of_type("ShuffleCard")
            if shuffles:
                view.say(random.choice(self._shuffle_quotes))
                return PlayCardAction(card=shuffles[0])
            
            # Must draw - hope we have defuse
            return DrawCardAction()
        
        # =====================================================================
        # PHASE 2: INTEL - Use See the Future heavily to eliminate guessing
        # =====================================================================
        
        # We need intel if we don't know what's coming
        no_current_intel = (safe_draws == 0) and (
            self._deck_shuffled_since_peek or not self._known_top_cards
        )
        
        # Use STF aggressively when:
        # 1. We don't have current intel, OR
        # 2. Risk is above 20% and we're uncertain
        risk_threshold = 0.20
        should_use_stf = no_current_intel or (
            explosion_prob > risk_threshold and safe_draws == 0
        )
        
        if should_use_stf:
            stf = view.get_cards_of_type("SeeTheFutureCard")
            if stf:
                view.say(random.choice(self._smart_quotes))
                return PlayCardAction(card=stf[0])
        
        # =====================================================================
        # PHASE 3: COMBOS (priority order)
        # =====================================================================
        
        # 3a. Five Different - ONLY if Defuse is in discard pile
        five_cards = self._can_play_five_different(view)
        if five_cards:
            view.say("Retrieving that Defuse from the discard!")
            return PlayComboAction(cards=five_cards)
        
        # 3b. Three of a Kind - Target player with Defuse, steal it
        three_combo = self._can_play_three_of_kind(view)
        if three_combo:
            cards, target = three_combo
            view.say(f"I require your Defuse, {target}!")
            return PlayComboAction(cards=cards, target_player_id=target)
        
        # 3c. Two of a Kind - Random steal from likely Defuse holder
        two_combo = self._can_play_two_of_kind(view)
        if two_combo:
            cards, target = two_combo
            target_count = view.other_player_card_counts.get(target, 0)
            # Use if target has at least 2 cards
            if target_count >= 2:
                view.say(random.choice(self._steal_quotes))
                return PlayComboAction(cards=cards, target_player_id=target)
        
        # 3d. Favor - Use more aggressively to get cards
        favors = view.get_cards_of_type("FavorCard")
        if favors and view.other_players:
            target = self._get_strongest_opponent(view)
            if target:
                target_count = view.other_player_card_counts.get(target, 0)
                if target_count >= 2:
                    view.say("Hand over something good!")
                    return PlayCardAction(card=favors[0], target_player_id=target)
        
        # 3e. Strategic Attack - Attack vulnerable next player proactively
        next_player = self._get_next_player(view)
        if next_player:
            # Attack if next player used their Defuse (vulnerable!)
            if next_player in self._players_who_defused:
                attacks = view.get_cards_of_type("AttackCard")
                if attacks:
                    view.say("Targeting the vulnerable one!")
                    return PlayCardAction(card=attacks[0])
            
            # Also attack if next player has very few cards
            next_cards = view.other_player_card_counts.get(next_player, 0)
            if next_cards <= 2 and explosion_prob > 0.25:
                attacks = view.get_cards_of_type("AttackCard")
                if attacks:
                    view.say("You seem short on options!")
                    return PlayCardAction(card=attacks[0])
        
        # =====================================================================
        # PHASE 4: HIGH PROBABILITY - Evasive action
        # =====================================================================
        
        # Thresholds based on whether we have Defuse
        danger_threshold = 0.40 if has_defuse else 0.30
        
        if explosion_prob > danger_threshold:
            view.say(random.choice(self._danger_quotes))
            
            # Attack first
            attacks = view.get_cards_of_type("AttackCard")
            if attacks and view.other_players:
                view.say(random.choice(self._attack_quotes))
                return PlayCardAction(card=attacks[0])
            
            # Skip second
            skips = view.get_cards_of_type("SkipCard")
            if skips:
                view.say(random.choice(self._skip_quotes))
                return PlayCardAction(card=skips[0])
            
            # Shuffle third
            shuffles = view.get_cards_of_type("ShuffleCard")
            if shuffles:
                view.say(random.choice(self._shuffle_quotes))
                return PlayCardAction(card=shuffles[0])
        
        # =====================================================================
        # PHASE 5: DRAW - Probability is acceptable
        # =====================================================================
        
        if random.random() < 0.1:
            view.say(random.choice(self._smart_quotes))
        
        return DrawCardAction()
    
    # =========================================================================
    # EVENT TRACKING
    # =========================================================================
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        """Track game state for probability calculations."""
        if event.event_type == EventType.BOT_CHAT:
            return
        
        # Track game start - everyone has 1 Defuse
        if event.event_type == EventType.GAME_START:
            player_ids = event.data.get("player_ids", [])
            self._initial_player_count = len(player_ids)
            # Everyone starts with a Defuse
            self._players_with_defuse = set(player_ids)
            if view.my_id in self._players_with_defuse:
                pass  # We know we have one
        
        # Track eliminations
        if event.event_type == EventType.PLAYER_ELIMINATED:
            self._eliminated_count += 1
            eliminated = event.player_id
            if eliminated:
                self._players_with_defuse.discard(eliminated)
                self._players_who_defused.discard(eliminated)
        
        # Track Defuse usage
        if event.event_type == EventType.EXPLODING_KITTEN_DEFUSED:
            player = event.player_id
            if player:
                self._players_who_defused.add(player)
                self._players_with_defuse.discard(player)
        
        # Track if Defuse is discarded
        if event.event_type == EventType.CARD_DISCARDED:
            card_type = event.data.get("card_type")
            if card_type == "DefuseCard":
                self._defuse_in_discard = True
        
        # Track cards played (some end up in discard)
        if event.event_type == EventType.CARD_PLAYED:
            card_type = event.data.get("card_type")
            if card_type == "DefuseCard":
                self._defuse_in_discard = True
        
        # Track shuffles (invalidates our knowledge)
        if event.event_type == EventType.DECK_SHUFFLED:
            self._known_top_cards = []
            self._deck_shuffled_since_peek = True
            self._cards_drawn_since_peek = 0
            self._just_shuffled = True  # Mark that we just shuffled
        
        # Track draws
        if event.event_type == EventType.CARD_DRAWN:
            self._cards_drawn_since_peek += 1
            # If someone draws from discard, they might take the Defuse
            if event.data.get("from") == "discard":
                card_type = event.data.get("card_type")
                if card_type == "DefuseCard":
                    self._defuse_in_discard = False
        
        # Track our See-the-Future
        if event.event_type == EventType.CARDS_PEEKED:
            if event.player_id == view.my_id:
                self._known_top_cards = list(event.data.get("card_types", []))
                self._deck_shuffled_since_peek = False
                self._cards_drawn_since_peek = 0
        
        # Track kitten insertions (invalidates our knowledge if not us)
        if event.event_type == EventType.EXPLODING_KITTEN_INSERTED:
            if event.player_id != view.my_id:
                self._known_top_cards = []
                self._deck_shuffled_since_peek = True
        
        # Check discard pile for Defuse (belt and suspenders)
        for card in view.discard_pile:
            if card.card_type == "DefuseCard":
                self._defuse_in_discard = True
                break
    
    # =========================================================================
    # REACT
    # =========================================================================
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        """
        Decide whether to nope an action.
        
        Einstein ALWAYS nopes hurtful actions against himself!
        """
        import random
        
        nopes = view.get_cards_of_type("NopeCard")
        if nopes and self._should_nope(triggering_event, view):
            view.say(random.choice(self._nope_quotes))
            return PlayCardAction(card=nopes[0])
        
        return None
    
    # =========================================================================
    # DEFUSE POSITION
    # =========================================================================
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        """
        Choose where to place the defused kitten.
        
        Strategy:
        - Target a player who likely LACKS Defuse (used one, or few cards)
        - Calculate how many draws until it reaches them
        - Place kitten at that position
        """
        import random
        
        view.say(random.choice(self._defuse_quotes))
        
        if draw_pile_size <= 1:
            return 0
        
        # Find the most vulnerable opponent
        # Priority: 1) Already used Defuse, 2) Fewest cards
        most_vulnerable = None
        
        for player in view.other_players:
            if player in self._players_who_defused:
                most_vulnerable = player
                break
        
        if most_vulnerable is None:
            most_vulnerable = self._get_weakest_opponent(view)
        
        # Calculate their position in turn order from us
        if most_vulnerable:
            turn_order = list(view.turn_order)
            if view.my_id in turn_order:
                my_idx = turn_order.index(view.my_id)
                alive = set(view.other_players) | {view.my_id}
                
                steps = 0
                for i in range(1, len(turn_order)):
                    candidate = turn_order[(my_idx + i) % len(turn_order)]
                    if candidate in alive:
                        steps += 1
                        if candidate == most_vulnerable:
                            break
                
                # Place kitten so it's drawn on their turn
                target_pos = max(0, min(steps - 1, draw_pile_size))
                return target_pos
        
        # Default: put it near the top for next player
        return random.randint(0, min(1, draw_pile_size))
    
    # =========================================================================
    # CARD TO GIVE
    # =========================================================================
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        """Give the least valuable card when targeted by Favor."""
        import random
        
        hand = list(view.my_hand)
        
        # Priority: Cat cards > Skip/Shuffle > STF > Attack > Favor > Nope > Defuse
        
        cats = [c for c in hand if "Cat" in c.card_type]
        if cats:
            return random.choice(cats)
        
        expendable = [c for c in hand if c.card_type in ("SkipCard", "ShuffleCard")]
        if expendable:
            return random.choice(expendable)
        
        stf = [c for c in hand if c.card_type == "SeeTheFutureCard"]
        if stf:
            return random.choice(stf)
        
        attacks = [c for c in hand if c.card_type == "AttackCard"]
        if attacks:
            return random.choice(attacks)
        
        favors = [c for c in hand if c.card_type == "FavorCard"]
        if favors:
            return random.choice(favors)
        
        non_critical = [c for c in hand if c.card_type not in ("NopeCard", "DefuseCard")]
        if non_critical:
            return random.choice(non_critical)
        
        non_defuse = [c for c in hand if c.card_type != "DefuseCard"]
        if non_defuse:
            return random.choice(non_defuse)
        
        return random.choice(hand)
    
    # =========================================================================
    # ON EXPLODE
    # =========================================================================
    
    def on_explode(self, view: BotView) -> None:
        """Famous last words."""
        import random
        view.say(random.choice(self._death_quotes))