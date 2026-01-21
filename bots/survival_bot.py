"""
==============================================================================
SURVIVAL BOT - A Smart Bot That Prioritizes Self-Preservation
==============================================================================

This bot focuses on survival above all else. It strategically:
- Nopes any action that directly threatens it (Attack, Favor targeting me)
- Uses See the Future to check for danger before drawing
- Uses Skip/Attack to avoid drawing when an Exploding Kitten is on top
- Places defused kittens at optimal positions for opponents
- Tracks opponents and game state for informed decisions
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


class SurvivalBot(Bot):
    """
    A survival-focused bot that prioritizes staying alive.
    
    Strategy:
    1. ALWAYS Nope attacks and favors directed at me
    2. Use See the Future before drawing to check for danger
    3. Use Skip/Attack if an Exploding Kitten is on top
    4. Place defused kittens strategically to harm opponents
    5. Conserve Nope cards for defensive use only
    """
    
    def __init__(self) -> None:
        """Initialize the bot with survival state tracking."""
        # Track the top cards of the draw pile (from See the Future)
        self._known_top_cards: list[str] = []
        
        # Track how many cards we've "consumed" from known top
        # (when someone draws or shuffles, this knowledge may be invalid)
        self._cards_drawn_since_peek: int = 0
        
        # Track if deck was shuffled since our last peek
        self._deck_shuffled_since_peek: bool = False
        
        # Survival-related chat phrases
        self._survival_taunts: list[str] = [
            "I refuse to die!",
            "You can't touch me!",
            "Safety first, always.",
            "Survival of the smartest!",
            "Not today, kittens!",
            "I've got nine lives too!",
        ]
        
        self._nope_phrases: list[str] = [
            "NOPE! Not gonna happen!",
            "Nice try, but NO.",
            "I don't think so!",
            "Did you really think that would work on ME?",
            "Denied!",
            "Get that away from me!",
        ]
        
        self._defuse_phrases: list[str] = [
            "Nice try, kitty! Better luck next time!",
            "Not today, death. Not today.",
            "I'm a survivor!",
            "*calmly defuses* You underestimate me.",
            "Ha! I've prepared for this moment!",
        ]
        
        self._attack_phrases: list[str] = [
            "YOUR problem now!",
            "Catch THIS!",
            "Tag, you're it!",
            "Pass the danger along!",
        ]
        
        self._skip_phrases: list[str] = [
            "Nope, not drawing. Too risky.",
            "I'll pass on that draw, thanks.",
            "Skipping to safety!",
        ]
        
        self._see_future_phrases: list[str] = [
            "*peeks nervously*",
            "Knowledge is survival!",
            "Let me see what's coming...",
        ]
        
        self._explosion_phrases: list[str] = [
            "This... wasn't part of the plan...",
            "Impossible! I was so careful!",
            "Tell them... I tried...",
            "At least I lasted this long!",
        ]
    
    @property
    def name(self) -> str:
        """Return the bot's name."""
        return "SurvivalBot"
    
    # =========================================================================
    # HELPER: Get the next player in turn order
    # =========================================================================
    
    def _get_next_player(self, view: BotView) -> str | None:
        """
        Get the ID of the next player after us in turn order.
        
        Inputs: view - The bot's view of the game
        Returns: The next player's ID, or None if we can't determine
        """
        if not view.other_players:
            return None
        
        turn_order = list(view.turn_order)
        if view.my_id not in turn_order:
            return view.other_players[0] if view.other_players else None
        
        my_index = turn_order.index(view.my_id)
        alive_players = set(view.other_players) | {view.my_id}
        
        # Find next alive player after me
        for i in range(1, len(turn_order)):
            next_index = (my_index + i) % len(turn_order)
            if turn_order[next_index] in alive_players:
                if turn_order[next_index] != view.my_id:
                    return turn_order[next_index]
        
        return view.other_players[0] if view.other_players else None
    
    # =========================================================================
    # HELPER: Check if we know the top card is dangerous
    # =========================================================================
    
    def _is_top_card_dangerous(self) -> bool:
        """
        Check if we know an Exploding Kitten is on top.
        
        Returns: True if we're certain the top card is an Exploding Kitten
        """
        if self._deck_shuffled_since_peek:
            return False
        
        if not self._known_top_cards:
            return False
        
        # Account for cards drawn since we peeked
        effective_index = self._cards_drawn_since_peek
        if effective_index < len(self._known_top_cards):
            return "ExplodingKittenCard" in self._known_top_cards[effective_index]
        
        return False
    
    # =========================================================================
    # HELPER: Find possible combos
    # =========================================================================
    
    def _find_possible_combos(
        self, hand: tuple[Card, ...]
    ) -> list[tuple[str, tuple[Card, ...]]]:
        """
        Find all possible combos in the given hand.
        
        Inputs: hand - The bot's current hand
        Returns: List of (combo_type, cards) tuples
        """
        combos: list[tuple[str, tuple[Card, ...]]] = []
        
        # Filter to only cards that can combo
        combo_cards = [c for c in hand if c.can_combo()]
        
        if not combo_cards:
            return combos
        
        # Group cards by type
        by_type: dict[str, list[Card]] = {}
        for card in combo_cards:
            if card.card_type not in by_type:
                by_type[card.card_type] = []
            by_type[card.card_type].append(card)
        
        # Check for two-of-a-kind and three-of-a-kind
        for card_type, cards_of_type in by_type.items():
            if len(cards_of_type) >= 3:
                combos.append(("three_of_a_kind", tuple(cards_of_type[:3])))
            elif len(cards_of_type) >= 2:
                combos.append(("two_of_a_kind", tuple(cards_of_type[:2])))
        
        # Check for five different card types
        if len(by_type) >= 5:
            five_cards: list[Card] = []
            for card_type in list(by_type.keys())[:5]:
                five_cards.append(by_type[card_type][0])
            combos.append(("five_different", tuple(five_cards)))
        
        return combos
    
    # =========================================================================
    # HELPER: Check if an event is targeting me
    # =========================================================================
    
    def _is_targeting_me(self, event: GameEvent, view: BotView) -> bool:
        """
        Check if a game event is targeting this bot.
        
        Inputs:
            event - The game event to check
            view - The current game view
        Returns: True if this event targets me
        """
        # Check for direct targeting in event data
        target = event.data.get("target_player_id")
        if target == view.my_id:
            return True
        
        # Check for Attack card (targets next player)
        card_type = event.data.get("card_type")
        if card_type == "AttackCard":
            # Attack targets next player in turn order from the player who played it
            attacker_id = event.player_id
            if attacker_id and attacker_id != view.my_id:
                # Check if we are the next player after the attacker
                turn_order = list(view.turn_order)
                if attacker_id in turn_order and view.my_id in turn_order:
                    attacker_index = turn_order.index(attacker_id)
                    alive_players = set(view.other_players) | {view.my_id}
                    
                    for i in range(1, len(turn_order)):
                        next_index = (attacker_index + i) % len(turn_order)
                        candidate = turn_order[next_index]
                        if candidate in alive_players:
                            return candidate == view.my_id
        
        return False
    
    # =========================================================================
    # HELPER: Should we Nope this event?
    # =========================================================================
    
    def _should_nope(self, event: GameEvent, view: BotView) -> bool:
        """
        Decide if we should Nope this event.
        
        SURVIVAL RULE: Always Nope attacks and favors targeting ME!
        
        Inputs:
            event - The triggering event
            view - Current game view
        Returns: True if we should play a Nope
        """
        card_type = event.data.get("card_type")
        
        # Always Nope attacks targeting me
        if card_type == "AttackCard" and self._is_targeting_me(event, view):
            return True
        
        # Always Nope favors targeting me
        if card_type == "FavorCard" and self._is_targeting_me(event, view):
            return True
        
        # Nope combo steals targeting me
        combo_type = event.data.get("combo_type")
        if combo_type in ("two_of_a_kind", "three_of_a_kind"):
            if self._is_targeting_me(event, view):
                return True
        
        return False
    
    # =========================================================================
    # REQUIRED: take_turn
    # =========================================================================
    
    def take_turn(self, view: BotView) -> Action:
        """
        Decide what to do on my turn.
        
        SURVIVAL STRATEGY:
        1. If danger is known on top -> Skip or Attack (avoid drawing)
        2. If unsure -> Use See the Future to check
        3. If safe or no alternatives -> Draw
        
        Args:
            view: The bot's view of the game state
            
        Returns:
            The action to take
        """
        import random
        
        hand = view.my_hand
        
        # =====================================================================
        # PHASE 1: Check if we KNOW danger is on top
        # =====================================================================
        
        if self._is_top_card_dangerous():
            # DANGER! Use Skip or Attack to avoid drawing
            
            # Prefer Skip (doesn't affect others much)
            skip_cards = view.get_cards_of_type("SkipCard")
            if skip_cards:
                phrase = random.choice(self._skip_phrases)
                view.say(phrase)
                return PlayCardAction(card=skip_cards[0])
            
            # Use Attack to pass the bomb to next player
            attack_cards = view.get_cards_of_type("AttackCard")
            if attack_cards and view.other_players:
                phrase = random.choice(self._attack_phrases)
                view.say(phrase)
                return PlayCardAction(card=attack_cards[0])
            
            # Try Shuffle to randomize the danger
            shuffle_cards = view.get_cards_of_type("ShuffleCard")
            if shuffle_cards:
                view.say("Let's mix things up...")
                return PlayCardAction(card=shuffle_cards[0])
        
        # =====================================================================
        # PHASE 2: If we don't know what's on top, use See the Future
        # =====================================================================
        
        if not self._known_top_cards or self._deck_shuffled_since_peek:
            see_future = view.get_cards_of_type("SeeTheFutureCard")
            if see_future:
                phrase = random.choice(self._see_future_phrases)
                view.say(phrase)
                return PlayCardAction(card=see_future[0])
        
        # =====================================================================
        # PHASE 3: Offensive plays (only if safe or have backup)
        # =====================================================================
        
        # If we have 2+ Defuse cards, we can afford to be more aggressive
        defuse_count = view.count_cards_of_type("DefuseCard")
        nope_count = view.count_cards_of_type("NopeCard")
        
        # Try combos to steal Defuse/Nope from opponents (if we're well-stocked)
        if defuse_count >= 2 or (defuse_count >= 1 and nope_count >= 2):
            possible_combos = self._find_possible_combos(hand)
            for combo_type, combo_cards in possible_combos:
                if combo_type in ("two_of_a_kind", "three_of_a_kind"):
                    if view.other_players:
                        # Target player with most cards (likely has good stuff)
                        target = max(
                            view.other_players,
                            key=lambda p: view.other_player_card_counts.get(p, 0)
                        )
                        phrase = random.choice(self._survival_taunts)
                        view.say(phrase)
                        return PlayComboAction(cards=combo_cards, target_player_id=target)
        
        # Play Favor if we're well-defended
        if defuse_count >= 1 and nope_count >= 1:
            favor_cards = view.get_cards_of_type("FavorCard")
            if favor_cards and view.other_players:
                target = max(
                    view.other_players,
                    key=lambda p: view.other_player_card_counts.get(p, 0)
                )
                view.say("Give me something nice!")
                return PlayCardAction(card=favor_cards[0], target_player_id=target)
        
        # =====================================================================
        # PHASE 4: Draw a card (hopefully safe!)
        # =====================================================================
        
        # Small chance to taunt before drawing
        if random.random() < 0.2:
            view.say(random.choice(self._survival_taunts))
        
        return DrawCardAction()
    
    # =========================================================================
    # REQUIRED: on_event
    # =========================================================================
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        """
        React to game events for state tracking.
        
        We track:
        - Deck shuffles (invalidates our See the Future knowledge)
        - Card draws (shifts our known top cards)
        - See the Future results (updates our knowledge)
        
        Args:
            event: The event that occurred
            view: Current game view
        """
        # Skip chat events
        if event.event_type == EventType.BOT_CHAT:
            return
        
        # Track deck shuffles
        if event.event_type == EventType.DECK_SHUFFLED:
            self._known_top_cards = []
            self._deck_shuffled_since_peek = True
            self._cards_drawn_since_peek = 0
        
        # Track card draws (shifts top card knowledge)
        if event.event_type == EventType.CARD_DRAWN:
            self._cards_drawn_since_peek += 1
        
        # Track our own See the Future results
        if event.event_type == EventType.CARDS_PEEKED:
            if event.player_id == view.my_id:
                # Update our knowledge from the peek
                peeked = event.data.get("card_types", [])
                self._known_top_cards = list(peeked)
                self._deck_shuffled_since_peek = False
                self._cards_drawn_since_peek = 0
        
        # Track Exploding Kitten insertions (might update our knowledge)
        if event.event_type == EventType.EXPLODING_KITTEN_INSERTED:
            # We don't know exactly where, but deck state changed
            # Only invalidate if we weren't the one who inserted it
            if event.player_id != view.my_id:
                # Our knowledge is now potentially stale
                self._known_top_cards = []
                self._deck_shuffled_since_peek = True
    
    # =========================================================================
    # REQUIRED: react
    # =========================================================================
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        """
        Decide whether to play a Nope card.
        
        SURVIVAL RULE: ALWAYS Nope attacks and favors targeting me!
        
        Args:
            view: Current game view
            triggering_event: The event we can react to
            
        Returns:
            PlayCardAction with Nope, or None to decline
        """
        import random
        
        nope_cards = view.get_cards_of_type("NopeCard")
        
        if nope_cards and self._should_nope(triggering_event, view):
            phrase = random.choice(self._nope_phrases)
            view.say(phrase)
            return PlayCardAction(card=nope_cards[0])
        
        return None
    
    # =========================================================================
    # REQUIRED: choose_defuse_position
    # =========================================================================
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        """
        Choose where to put the Exploding Kitten after defusing.
        
        STRATEGY: Put it at position 1 (second from top) so the next player
        draws it right away! But if there's only 1 card, put it at top.
        
        Args:
            view: Current game view
            draw_pile_size: Size of the draw pile
            
        Returns:
            Position to insert (0 = top)
        """
        import random
        
        phrase = random.choice(self._defuse_phrases)
        view.say(phrase)
        
        # Put it near the top so next player gets it!
        # Position 0 = very top (next draw)
        # We put it at position 0-1 to maximize chance next player gets it
        if draw_pile_size <= 1:
            return 0  # Put at top
        
        # Put it either at top (0) or second (1) - next player's problem!
        return random.randint(0, min(1, draw_pile_size))
    
    # =========================================================================
    # REQUIRED: choose_card_to_give
    # =========================================================================
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        """
        Choose which card to give when targeted by Favor.
        
        SURVIVAL STRATEGY:
        - NEVER give Defuse or Nope (our lifelines!)
        - Give the least useful card possible
        
        Args:
            view: Current game view
            requester_id: Who's asking for the card
            
        Returns:
            The card to give away
        """
        import random
        
        hand = list(view.my_hand)
        view.say("Fine... take this useless thing.")
        
        # Priority: Keep Defuse and Nope at all costs!
        
        # 1. Give a cat card (useless alone)
        cat_cards = [c for c in hand if "Cat" in c.card_type]
        if cat_cards:
            return random.choice(cat_cards)
        
        # 2. Give Skip or Shuffle (least critical)
        low_value = [c for c in hand if c.card_type in ("SkipCard", "ShuffleCard")]
        if low_value:
            return random.choice(low_value)
        
        # 3. Give See the Future (nice to have, not critical)
        see_future = [c for c in hand if c.card_type == "SeeTheFutureCard"]
        if see_future:
            return random.choice(see_future)
        
        # 4. Give Attack (useful but not survival-critical)
        attack_cards = [c for c in hand if c.card_type == "AttackCard"]
        if attack_cards:
            return random.choice(attack_cards)
        
        # 5. Avoid giving Nope if possible
        non_nope = [c for c in hand if c.card_type != "NopeCard" and c.card_type != "DefuseCard"]
        if non_nope:
            return random.choice(non_nope)
        
        # 6. Avoid giving Defuse at all costs
        non_defuse = [c for c in hand if c.card_type != "DefuseCard"]
        if non_defuse:
            return random.choice(non_defuse)
        
        # 7. Last resort: have to give something
        return random.choice(hand)
    
    # =========================================================================
    # REQUIRED: on_explode
    # =========================================================================
    
    def on_explode(self, view: BotView) -> None:
        """
        Say last words before being eliminated.
        
        Args:
            view: Current game view
        """
        import random
        
        phrase = random.choice(self._explosion_phrases)
        view.say(phrase)
