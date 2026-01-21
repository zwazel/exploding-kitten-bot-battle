"""
==============================================================================
EINSTEIN BOT - The Probability Calculator
==============================================================================

Einstein leverages probability calculations to make optimal decisions.
Strategy:
1. Calculate the probability of drawing an Exploding Kitten at any moment
2. Hoard cards to build a powerful hand (more options = more control)
3. Only play cards when strategically valuable (avoid wasting resources)
4. Use See the Future to eliminate uncertainty before critical draws
5. Strategically place defused kittens based on opponent threat assessment
6. Nope only when the expected value is positive (protect self or hurt leaders)
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
    A probability-focused bot that calculates risk and hoards cards.
    
    Core Philosophy:
    - Knowledge is power (track everything)
    - Calculate expected values before acting
    - Hoard cards unless playing provides clear advantage
    - Minimize personal risk while maximizing opponent risk
    """
    
    def __init__(self) -> None:
        """Initialize Einstein with state tracking."""
        # Track the top cards from See the Future
        self._known_top_cards: list[str] = []
        
        # Track draws since last peek
        self._cards_drawn_since_peek: int = 0
        
        # Track if deck was shuffled since peek
        self._deck_shuffled_since_peek: bool = False
        
        # Track number of Exploding Kittens in deck
        # Initial = num_players - 1, but we update as they explode
        self._known_kittens_in_deck: int | None = None
        
        # Track eliminated players to calculate remaining kittens
        self._eliminated_players: set[str] = set()
        
        # Track how many players we started with
        self._initial_player_count: int | None = None
        
        # Track defuse count in our hand (for risk assessment)
        self._last_known_defuse_count: int = 0
        
        # Einstein quotes for personality
        self._genius_quotes: list[str] = [
            "E = mc² ... of course.",
            "God does not play dice with the universe... but I do!",
            "Imagination is more important than knowledge.",
            "The only source of knowledge is experience.",
            "I have no special talents. I am only passionately curious.",
        ]
        
        self._calculation_quotes: list[str] = [
            "Calculating probabilities...",
            "The math says: safe to proceed.",
            "According to my calculations...",
            "Interesting probability distribution...",
            "Let me think about this relatively...",
        ]
        
        self._danger_quotes: list[str] = [
            "The probability of catastrophe is too high!",
            "My calculations indicate danger ahead!",
            "This requires evasive action!",
            "Theory suggests I should skip this!",
        ]
        
        self._defuse_quotes: list[str] = [
            "Elementary physics, my dear kitten.",
            "As I predicted.",
            "E = mc²... and D = Defused!",
            "Probability of survival: now 100%.",
        ]
        
        self._nope_quotes: list[str] = [
            "Your theory has been disproven.",
            "That hypothesis is rejected!",
            "Peer review: DENIED.",
            "Counter-example provided!",
        ]
        
        self._explosion_quotes: list[str] = [
            "Even geniuses make errors occasionally...",
            "The probability was supposed to be lower...",
            "My calculations... were wrong?!",
            "Relativity caught up with me...",
        ]

    @property
    def name(self) -> str:
        """Return the bot's name."""
        return "Einstein"
    
    # =========================================================================
    # PROBABILITY CALCULATIONS
    # =========================================================================
    
    def _calculate_explosion_probability(self, view: BotView) -> float:
        """
        Calculate the probability of drawing an Exploding Kitten.
        
        P(explosion) = kittens_in_deck / draw_pile_size
        
        Inputs: view - The bot's view of the game
        Returns: Probability from 0.0 to 1.0
        """
        draw_pile_size = view.draw_pile_count
        
        if draw_pile_size == 0:
            return 0.0  # Empty deck = no risk
        
        # Estimate kittens in deck
        kittens_in_deck = self._estimate_kittens_in_deck(view)
        
        return kittens_in_deck / draw_pile_size
    
    def _estimate_kittens_in_deck(self, view: BotView) -> int:
        """
        Estimate how many Exploding Kittens are in the deck.
        
        Rule: num_players - 1 kittens at start
        After eliminations, some kittens may have caused explosions.
        
        Inputs: view - The bot's view of the game
        Returns: Estimated number of kittens in deck
        """
        if self._known_kittens_in_deck is not None:
            return self._known_kittens_in_deck
        
        # Initial estimate: (initial_players - 1) - eliminated_players
        # Each eliminated player took one kitten with them (usually)
        if self._initial_player_count is not None:
            initial_kittens = self._initial_player_count - 1
            eliminated = len(self._eliminated_players)
            return max(0, initial_kittens - eliminated)
        
        # Fallback: players_still_alive is a proxy
        # If 4 players playing, 3 kittens. If 1 eliminated, ~2 kittens left.
        total_players = len(view.other_players) + 1
        return max(0, total_players - 1)
    
    def _get_known_top_danger(self, positions: int = 1) -> bool:
        """
        Check if we know an Exploding Kitten is in the top N positions.
        
        Inputs: positions - How many top positions to check
        Returns: True if we're certain a kitten is in those positions
        """
        if self._deck_shuffled_since_peek:
            return False
        
        if not self._known_top_cards:
            return False
        
        # Account for cards drawn since we peeked
        effective_start = self._cards_drawn_since_peek
        effective_end = effective_start + positions
        
        # Check if any known position in range has an Exploding Kitten
        for i in range(effective_start, min(effective_end, len(self._known_top_cards))):
            if self._known_top_cards[i] == "ExplodingKittenCard":
                return True
        
        return False
    
    def _get_known_safe_draws(self) -> int:
        """
        Get the number of draws we KNOW are safe.
        
        Returns: Number of guaranteed safe draws (0 if unknown)
        """
        if self._deck_shuffled_since_peek:
            return 0
        
        if not self._known_top_cards:
            return 0
        
        safe_draws = 0
        effective_start = self._cards_drawn_since_peek
        
        for i in range(effective_start, len(self._known_top_cards)):
            if self._known_top_cards[i] == "ExplodingKittenCard":
                break
            safe_draws += 1
        
        return safe_draws
    
    # =========================================================================
    # STRATEGIC ASSESSMENTS
    # =========================================================================
    
    def _get_threat_level(self, player_id: str, view: BotView) -> float:
        """
        Assess how threatening an opponent is.
        
        Threat = card_count (more cards = more options = more dangerous)
        
        Inputs:
            player_id - The opponent to assess
            view - The bot's view of the game
        Returns: Threat score (higher = more threatening)
        """
        card_count = view.other_player_card_counts.get(player_id, 0)
        return float(card_count)
    
    def _get_most_threatening_player(self, view: BotView) -> str | None:
        """
        Find the opponent with the highest threat level.
        
        Inputs: view - The bot's view of the game
        Returns: Player ID of the most threatening opponent
        """
        if not view.other_players:
            return None
        
        return max(
            view.other_players,
            key=lambda p: self._get_threat_level(p, view)
        )
    
    def _get_next_player(self, view: BotView) -> str | None:
        """
        Get the next player in turn order after us.
        
        Inputs: view - The bot's view of the game
        Returns: Next player's ID or None
        """
        if not view.other_players:
            return None
        
        turn_order = list(view.turn_order)
        if view.my_id not in turn_order:
            return view.other_players[0]
        
        my_index = turn_order.index(view.my_id)
        alive_players = set(view.other_players) | {view.my_id}
        
        for i in range(1, len(turn_order)):
            next_index = (my_index + i) % len(turn_order)
            candidate = turn_order[next_index]
            if candidate in alive_players and candidate != view.my_id:
                return candidate
        
        return view.other_players[0]
    
    def _should_hoard(self, view: BotView) -> bool:
        """
        Decide if we should continue hoarding cards vs. playing.
        
        Einstein hoards when:
        - We have room to grow (not too many cards)
        - Explosion probability is acceptable
        - We have a defuse as insurance
        
        Inputs: view - The bot's view of the game
        Returns: True if we should hoard (just draw), False if we should play
        """
        explosion_prob = self._calculate_explosion_probability(view)
        has_defuse = view.has_card_type("DefuseCard")
        hand_size = len(view.my_hand)
        
        # If we KNOW the top is dangerous, don't hoard
        if self._get_known_top_danger():
            return False
        
        # If probability is very low (< 15%), hoard unless we have many cards
        if explosion_prob < 0.15:
            return hand_size < 12  # Keep hoarding up to 12 cards
        
        # If probability is moderate (15-30%) and we have defuse, continue hoarding
        if explosion_prob < 0.30 and has_defuse:
            return hand_size < 10  # More conservative threshold
        
        # If probability is higher, only hoard if we have defuse and small hand
        if explosion_prob < 0.40 and has_defuse:
            return hand_size < 8
        
        # High probability: stop hoarding, play defensively
        return False
    
    def _calculate_play_value(
        self, card: Card, view: BotView
    ) -> float:
        """
        Calculate the strategic value of playing a specific card.
        
        Higher value = more beneficial to play now.
        Negative value = should save for later.
        
        Inputs:
            card - The card to evaluate
            view - The bot's view of the game
        Returns: Value score (higher = more valuable to play)
        """
        card_type = card.card_type
        explosion_prob = self._calculate_explosion_probability(view)
        has_defuse = view.has_card_type("DefuseCard")
        known_danger = self._get_known_top_danger()
        
        # Skip Card: Value increases with danger
        if card_type == "SkipCard":
            if known_danger:
                return 100.0  # Critical play!
            if explosion_prob > 0.4:
                return 50.0
            if explosion_prob > 0.25:
                return 20.0
            return -10.0  # Save it for when needed
        
        # Attack Card: Similar to skip but passes danger
        if card_type == "AttackCard":
            if known_danger:
                return 95.0  # Almost as good as skip
            if explosion_prob > 0.4:
                return 45.0
            if explosion_prob > 0.25:
                return 15.0
            return -15.0  # Save it
        
        # See the Future: Valuable when uncertain
        if card_type == "SeeTheFutureCard":
            if self._deck_shuffled_since_peek or not self._known_top_cards:
                safe_draws = self._get_known_safe_draws()
                if safe_draws == 0:
                    return 30.0  # High value - we need intel
            return -5.0  # We already know the future
        
        # Shuffle: Valuable when danger is known on top
        if card_type == "ShuffleCard":
            if known_danger:
                return 80.0  # Reroll the danger
            return -20.0  # Don't waste it
        
        # Favor: Moderate value for stealing cards
        if card_type == "FavorCard":
            if view.other_players:
                target = self._get_most_threatening_player(view)
                if target:
                    target_cards = view.other_player_card_counts.get(target, 0)
                    if target_cards > 5:
                        return 10.0  # Worth using
            return -10.0  # Save it
        
        # Nope: Never play proactively
        if card_type == "NopeCard":
            return -100.0  # Only for reactions
        
        # Defuse: Never play proactively
        if card_type == "DefuseCard":
            return -200.0  # This is our lifeline
        
        # Cat cards: Only valuable in combos
        if "Cat" in card_type:
            return -50.0  # Save for combos
        
        return 0.0
    
    def _find_best_combo(
        self, view: BotView
    ) -> tuple[str, tuple[Card, ...], str | None] | None:
        """
        Find the best combo to play, if any is worthwhile.
        
        Inputs: view - The bot's view of the game
        Returns: (combo_type, cards, target_id) or None
        """
        hand = view.my_hand
        
        # Group cards by type
        by_type: dict[str, list[Card]] = {}
        for card in hand:
            if card.can_combo():
                if card.card_type not in by_type:
                    by_type[card.card_type] = []
                by_type[card.card_type].append(card)
        
        # Einstein prefers three-of-a-kind (can request specific card)
        for card_type, cards_of_type in by_type.items():
            if len(cards_of_type) >= 3 and view.other_players:
                # Target the player with most cards
                target = self._get_most_threatening_player(view)
                return ("three_of_a_kind", tuple(cards_of_type[:3]), target)
        
        # Two-of-a-kind if we have many duplicates (4+) - can spare 2
        for card_type, cards_of_type in by_type.items():
            if len(cards_of_type) >= 4 and view.other_players:
                target = self._get_most_threatening_player(view)
                return ("two_of_a_kind", tuple(cards_of_type[:2]), target)
        
        # Five different for discard pile if valuable cards there
        if len(by_type) >= 5:
            # Check if discard pile has defuse or nope
            valuable_in_discard = [
                c for c in view.discard_pile
                if c.card_type in ("DefuseCard", "NopeCard")
            ]
            if valuable_in_discard:
                five_cards: list[Card] = []
                for card_type in list(by_type.keys())[:5]:
                    five_cards.append(by_type[card_type][0])
                return ("five_different", tuple(five_cards), None)
        
        return None
    
    # =========================================================================
    # NOPE DECISION LOGIC
    # =========================================================================
    
    def _is_targeting_me(self, event: GameEvent, view: BotView) -> bool:
        """
        Check if an event is targeting this bot.
        
        Inputs:
            event - The game event to check
            view - Current game view
        Returns: True if targeting me
        """
        # Direct targeting
        target = event.data.get("target_player_id")
        if target == view.my_id:
            return True
        
        # Attack targets next player
        card_type = event.data.get("card_type")
        if card_type == "AttackCard":
            attacker_id = event.player_id
            if attacker_id and attacker_id != view.my_id:
                next_after_attacker = self._get_next_player_after(
                    attacker_id, view
                )
                if next_after_attacker == view.my_id:
                    return True
        
        return False
    
    def _get_next_player_after(
        self, player_id: str, view: BotView
    ) -> str | None:
        """
        Get the next player after a specific player.
        
        Inputs:
            player_id - The player to start from
            view - Current game view
        Returns: Next player's ID
        """
        turn_order = list(view.turn_order)
        if player_id not in turn_order:
            return None
        
        player_index = turn_order.index(player_id)
        alive_players = set(view.other_players) | {view.my_id}
        
        for i in range(1, len(turn_order)):
            next_index = (player_index + i) % len(turn_order)
            candidate = turn_order[next_index]
            if candidate in alive_players:
                return candidate
        
        return None
    
    def _should_nope(self, event: GameEvent, view: BotView) -> bool:
        """
        Decide if we should Nope this event.
        
        Einstein's Nope Strategy:
        1. ALWAYS Nope attacks/favors/combos targeting me
        2. Consider Noping actions that benefit leading players
        3. Conserve Nopes otherwise (they're valuable)
        
        Inputs:
            event - The triggering event
            view - Current game view
        Returns: True if we should play a Nope
        """
        card_type = event.data.get("card_type")
        combo_type = event.data.get("combo_type")
        
        # ALWAYS Nope attacks targeting me
        if card_type == "AttackCard" and self._is_targeting_me(event, view):
            return True
        
        # ALWAYS Nope favors targeting me
        if card_type == "FavorCard" and self._is_targeting_me(event, view):
            return True
        
        # ALWAYS Nope combos targeting me
        if combo_type in ("two_of_a_kind", "three_of_a_kind"):
            if self._is_targeting_me(event, view):
                return True
        
        # Consider Noping See the Future by leading player
        # (but only if we have 2+ Nopes)
        nope_count = view.count_cards_of_type("NopeCard")
        if nope_count >= 2:
            actor = event.player_id
            if actor and card_type == "SeeTheFutureCard":
                # If this player is leading (most cards), consider noping
                if actor == self._get_most_threatening_player(view):
                    threat = self._get_threat_level(actor, view)
                    if threat > 8:  # Very high card count
                        return True
        
        return False
    
    # =========================================================================
    # REQUIRED: take_turn
    # =========================================================================
    
    def take_turn(self, view: BotView) -> Action:
        """
        Einstein's turn logic:
        
        1. If danger is KNOWN on top → Avoid drawing (Skip/Attack/Shuffle)
        2. If uncertain → Use See the Future for intel
        3. If safe or low probability → Hoard (just draw)
        4. If probability is high → Play best card
        
        Inputs: view - The bot's view of the game state
        Returns: The action to take
        """
        import random
        
        hand = view.my_hand
        explosion_prob = self._calculate_explosion_probability(view)
        known_danger = self._get_known_top_danger()
        has_defuse = view.has_card_type("DefuseCard")
        
        # =====================================================================
        # PHASE 1: KNOWN DANGER - Immediate evasive action
        # =====================================================================
        
        if known_danger:
            view.say(random.choice(self._danger_quotes))
            
            # Prefer Skip (least waste)
            skip_cards = view.get_cards_of_type("SkipCard")
            if skip_cards:
                return PlayCardAction(card=skip_cards[0])
            
            # Attack passes danger to next player
            attack_cards = view.get_cards_of_type("AttackCard")
            if attack_cards and view.other_players:
                return PlayCardAction(card=attack_cards[0])
            
            # Shuffle randomizes the danger
            shuffle_cards = view.get_cards_of_type("ShuffleCard")
            if shuffle_cards:
                return PlayCardAction(card=shuffle_cards[0])
            
            # Last resort: Must draw (hopefully have defuse)
            if has_defuse:
                view.say("I have prepared for this eventuality.")
            return DrawCardAction()
        
        # =====================================================================
        # PHASE 2: GATHER INTELLIGENCE
        # =====================================================================
        
        # If we don't have current intel, get it
        safe_draws = self._get_known_safe_draws()
        need_intel = (
            safe_draws == 0 and
            (self._deck_shuffled_since_peek or not self._known_top_cards)
        )
        
        if need_intel:
            see_future = view.get_cards_of_type("SeeTheFutureCard")
            if see_future:
                view.say(random.choice(self._calculation_quotes))
                return PlayCardAction(card=see_future[0])
        
        # =====================================================================
        # PHASE 3: HOARDING MODE
        # =====================================================================
        
        # If conditions are favorable, just draw to build our hand
        if self._should_hoard(view):
            if random.random() < 0.1:  # Occasional genius quote
                view.say(random.choice(self._genius_quotes))
            return DrawCardAction()
        
        # =====================================================================
        # PHASE 4: STRATEGIC PLAYS
        # =====================================================================
        
        # Find the best card to play based on value calculations
        playable_cards = [c for c in hand if c.can_play(view, is_own_turn=True)]
        
        if playable_cards:
            best_card = None
            best_value = -float("inf")
            
            for card in playable_cards:
                value = self._calculate_play_value(card, view)
                if value > best_value:
                    best_value = value
                    best_card = card
            
            # Only play if value is positive
            if best_card and best_value > 0:
                card_type = best_card.card_type
                
                # Skip or Attack need no target
                if card_type in ("SkipCard", "ShuffleCard", "SeeTheFutureCard"):
                    return PlayCardAction(card=best_card)
                
                # Attack might want to target specific player
                if card_type == "AttackCard":
                    return PlayCardAction(card=best_card)
                
                # Favor needs a target
                if card_type == "FavorCard" and view.other_players:
                    target = self._get_most_threatening_player(view)
                    if target:
                        return PlayCardAction(
                            card=best_card, target_player_id=target
                        )
        
        # Check for valuable combos
        combo = self._find_best_combo(view)
        if combo:
            combo_type, cards, target = combo
            if target:
                view.say(f"Theoretical analysis complete: stealing from {target}!")
                return PlayComboAction(cards=cards, target_player_id=target)
            else:
                # Five different combo (grab from discard)
                view.say("Recovering valuable research materials!")
                # Find defuse or nope in discard
                target_card = None
                for c in view.discard_pile:
                    if c.card_type == "DefuseCard":
                        target_card = c
                        break
                    if c.card_type == "NopeCard":
                        target_card = c
                if target_card:
                    return PlayComboAction(cards=cards, target_card=target_card)
        
        # =====================================================================
        # PHASE 5: DEFAULT - Draw
        # =====================================================================
        
        # If probability is acceptable or we have a defuse, draw
        if explosion_prob < 0.4 or has_defuse:
            if random.random() < 0.1:
                view.say(random.choice(self._calculation_quotes))
            return DrawCardAction()
        
        # High danger, no defuse - try any evasive action
        skip_cards = view.get_cards_of_type("SkipCard")
        if skip_cards:
            view.say("I must recalculate the odds!")
            return PlayCardAction(card=skip_cards[0])
        
        attack_cards = view.get_cards_of_type("AttackCard")
        if attack_cards and view.other_players:
            view.say("Passing this problem to a peer!")
            return PlayCardAction(card=attack_cards[0])
        
        # No choice but to draw
        view.say("The universe demands a draw...")
        return DrawCardAction()
    
    # =========================================================================
    # REQUIRED: on_event
    # =========================================================================
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        """
        Track game state for probability calculations.
        
        Inputs:
            event - The event that occurred
            view - Current game view
        """
        # Skip chat events
        if event.event_type == EventType.BOT_CHAT:
            return
        
        # Track game start to know initial player count
        if event.event_type == EventType.GAME_START:
            player_ids = event.data.get("player_ids", [])
            self._initial_player_count = len(player_ids)
            self._known_kittens_in_deck = self._initial_player_count - 1
        
        # Track eliminations
        if event.event_type == EventType.PLAYER_ELIMINATED:
            eliminated_id = event.player_id
            if eliminated_id:
                self._eliminated_players.add(eliminated_id)
                # An elimination usually means a kitten took them out
                # Reduce our estimate of kittens in deck
                if self._known_kittens_in_deck is not None:
                    self._known_kittens_in_deck = max(
                        0, self._known_kittens_in_deck - 1
                    )
        
        # Track deck shuffles (invalidates our knowledge)
        if event.event_type == EventType.DECK_SHUFFLED:
            self._known_top_cards = []
            self._deck_shuffled_since_peek = True
            self._cards_drawn_since_peek = 0
        
        # Track card draws (shifts our knowledge window)
        if event.event_type == EventType.CARD_DRAWN:
            self._cards_drawn_since_peek += 1
        
        # Track our own See the Future results
        if event.event_type == EventType.CARDS_PEEKED:
            if event.player_id == view.my_id:
                peeked = event.data.get("card_types", [])
                self._known_top_cards = list(peeked)
                self._deck_shuffled_since_peek = False
                self._cards_drawn_since_peek = 0
        
        # Track Exploding Kitten insertions from other players
        if event.event_type == EventType.EXPLODING_KITTEN_INSERTED:
            if event.player_id != view.my_id:
                # Our knowledge is now stale
                self._known_top_cards = []
                self._deck_shuffled_since_peek = True
        
        # Track defused kittens (kitten went back into deck)
        if event.event_type == EventType.EXPLODING_KITTEN_DEFUSED:
            # A defused kitten is STILL in the deck (not removed)
            # So no change to kitten count needed
            pass
    
    # =========================================================================
    # REQUIRED: react
    # =========================================================================
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        """
        Decide whether to Nope an event.
        
        Einstein only Nopes when:
        1. The action directly threatens him
        2. A leading player gains too much advantage
        
        Inputs:
            view - Current game view
            triggering_event - The event we can react to
        Returns: PlayCardAction with Nope, or None
        """
        import random
        
        nope_cards = view.get_cards_of_type("NopeCard")
        
        if nope_cards and self._should_nope(triggering_event, view):
            view.say(random.choice(self._nope_quotes))
            return PlayCardAction(card=nope_cards[0])
        
        return None
    
    # =========================================================================
    # REQUIRED: choose_defuse_position
    # =========================================================================
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        """
        Choose optimal position for the Exploding Kitten.
        
        Einstein's Strategy:
        - Place kitten where next player is most likely to draw it
        - Account for their likely card usage (Skip, Attack, etc.)
        - Position 1-2 is usually optimal (not 0, as they might Skip)
        
        Inputs:
            view - Current game view
            draw_pile_size - Size of draw pile
        Returns: Position to insert (0 = top)
        """
        import random
        
        view.say(random.choice(self._defuse_quotes))
        
        if draw_pile_size == 0:
            return 0
        
        if draw_pile_size == 1:
            return 0  # Only one spot
        
        # Get next player's card count
        next_player = self._get_next_player(view)
        if next_player:
            next_cards = view.other_player_card_counts.get(next_player, 0)
            
            # If they have many cards, they likely have Skip/Attack
            # Place kitten slightly deeper so Skip doesn't save them
            if next_cards > 6:
                # Place at position 2-3 (they might skip 1)
                return min(random.randint(2, 3), draw_pile_size)
            else:
                # They probably can't skip - put it at top
                return random.randint(0, min(1, draw_pile_size))
        
        # Default: near the top
        return random.randint(0, min(1, draw_pile_size))
    
    # =========================================================================
    # REQUIRED: choose_card_to_give
    # =========================================================================
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        """
        Choose which card to give when targeted by Favor.
        
        Einstein's Priority (always give least valuable):
        1. Cat cards (useless alone)
        2. Skip/Shuffle (expendable)
        3. See the Future (nice but not critical)
        4. Attack (useful but replaceable)
        5. NEVER give Nope or Defuse if avoidable
        
        Inputs:
            view - Current game view
            requester_id - Who's requesting
        Returns: Card to give away
        """
        import random
        
        hand = list(view.my_hand)
        
        view.say("Fine, take some of my early research...")
        
        # 1. Give cat cards first (worthless alone)
        cats = [c for c in hand if "Cat" in c.card_type]
        if cats:
            return random.choice(cats)
        
        # 2. Give Skip or Shuffle
        expendable = [c for c in hand if c.card_type in ("SkipCard", "ShuffleCard")]
        if expendable:
            return random.choice(expendable)
        
        # 3. Give See the Future
        stf = [c for c in hand if c.card_type == "SeeTheFutureCard"]
        if stf:
            return random.choice(stf)
        
        # 4. Give Attack
        attacks = [c for c in hand if c.card_type == "AttackCard"]
        if attacks:
            return random.choice(attacks)
        
        # 5. Give Favor back (if we have it)
        favors = [c for c in hand if c.card_type == "FavorCard"]
        if favors:
            return random.choice(favors)
        
        # 6. Avoid Nope
        non_nope = [c for c in hand if c.card_type != "NopeCard" and c.card_type != "DefuseCard"]
        if non_nope:
            return random.choice(non_nope)
        
        # 7. Avoid Defuse at all costs
        non_defuse = [c for c in hand if c.card_type != "DefuseCard"]
        if non_defuse:
            return random.choice(non_defuse)
        
        # 8. Last resort
        return random.choice(hand)
    
    # =========================================================================
    # REQUIRED: on_explode
    # =========================================================================
    
    def on_explode(self, view: BotView) -> None:
        """
        Famous last words.
        
        Inputs: view - Current game view
        """
        import random
        view.say(random.choice(self._explosion_quotes))