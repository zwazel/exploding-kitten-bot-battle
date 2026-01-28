"""
Bombocat 2.0 - Elite Strategic Exploding Kittens Bot

Strategy Philosophy:
1. Analyze input carefully: identify chances, risks, and opponent positions
2. Prioritize long-term advantages over short-term gains
3. Always choose the strategically optimal action
4. Dynamically adapt to opponents and anticipate their moves
5. Avoid unnecessary risks, maximize every opportunity
6. When options are similar, choose the one that harms opponents most
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


class OpponentProfile:
    """Track detailed information about a specific opponent."""
    
    def __init__(self, player_id: str) -> None:
        self.player_id = player_id
        self.defuses_used = 0
        self.cards_played: list[str] = []
        self.aggressive_plays = 0  # Attacks, Favors, Combos
        self.defensive_plays = 0  # Skips, Nopes
        self.last_known_card_count = 0
        self.cards_stolen_from_me = 0
        self.cards_given_to_me = 0
        self.nope_count = 0  # How many Nopes they've played
        self.has_seen_future = False  # Did they use SeeTheFuture recently?
        
    def update_card_count(self, count: int) -> None:
        self.last_known_card_count = count
        
    def record_play(self, card_type: str) -> None:
        self.cards_played.append(card_type)
        if card_type in ("AttackCard", "FavorCard"):
            self.aggressive_plays += 1
        elif card_type in ("SkipCard", "NopeCard"):
            self.defensive_plays += 1
            if card_type == "NopeCard":
                self.nope_count += 1
        elif card_type == "SeeTheFutureCard":
            self.has_seen_future = True
            
    def threat_level(self) -> float:
        """Calculate how dangerous this opponent is (0-1)."""
        # More cards = more dangerous
        card_threat = min(1.0, self.last_known_card_count / 7.0)
        # Aggressive players are more threatening
        aggression = self.aggressive_plays / max(1, len(self.cards_played) + 1)
        # Fewer defuses used = more lives left = more dangerous
        defuse_threat = max(0.0, 1.0 - (self.defuses_used * 0.35))
        # Players with Nopes are dangerous
        nope_threat = min(0.3, self.nope_count * 0.15)
        
        return (card_threat * 0.35 + aggression * 0.25 + defuse_threat * 0.3 + nope_threat * 0.1)
    
    def vulnerability(self) -> float:
        """Calculate how vulnerable this opponent is (0-1, higher = weaker)."""
        # Few cards = vulnerable
        card_vuln = max(0.0, 1.0 - min(1.0, self.last_known_card_count / 4.0))
        # Many defuses used = vulnerable
        defuse_vuln = min(1.0, self.defuses_used * 0.45)
        # Being attacked/stolen from = vulnerable
        harassment_vuln = min(0.3, self.cards_stolen_from_me * 0.1)
        
        return min(1.0, card_vuln * 0.5 + defuse_vuln * 0.4 + harassment_vuln * 0.1)


class GameStateTracker:
    """Advanced game state analysis with predictive modeling."""
    
    def __init__(self) -> None:
        self.opponents: dict[str, OpponentProfile] = {}
        self.known_top_cards: list[str] = []  # From SeeTheFuture
        self.total_players_start = 0
        self.kittens_defused_total = 0
        self.turn_count = 0
        self.cards_in_discard_by_type: dict[str, int] = {}
        self.my_cards_played: list[str] = []
        
    def get_opponent(self, player_id: str) -> OpponentProfile:
        if player_id not in self.opponents:
            self.opponents[player_id] = OpponentProfile(player_id)
        return self.opponents[player_id]
    
    def estimate_kitten_risk(self, view: BotView, my_defuses: int) -> float:
        """Estimate probability of drawing an Exploding Kitten with advanced heuristics."""
        if view.draw_pile_count == 0:
            return 1.0
            
        # Calculate expected kittens in deck
        num_players = len(view.other_players) + 1
        if self.total_players_start == 0:
            self.total_players_start = num_players
            
        initial_kittens = self.total_players_start - 1
        estimated_kittens = max(0, initial_kittens - self.kittens_defused_total)
        
        # If we know top cards from SeeTheFuture
        if self.known_top_cards:
            if len(self.known_top_cards) > 0 and self.known_top_cards[0] == "ExplodingKittenCard":
                return 1.0  # Certain death
            # Count kittens in known cards
            kittens_in_known = sum(1 for c in self.known_top_cards if c == "ExplodingKittenCard")
            if kittens_in_known == 0 and len(self.known_top_cards) >= 3:
                # We know top 3 are safe
                estimated_kittens = max(0, estimated_kittens - 0.7)
        
        base_risk = estimated_kittens / max(1, view.draw_pile_count)
        
        # Adjust for defuse count (exponential safety with more defuses)
        if my_defuses == 0:
            return 1.0  # No safety net = maximum risk
        elif my_defuses == 1:
            return min(1.0, base_risk * 1.4)  # Still very risky
        elif my_defuses == 2:
            return min(1.0, base_risk * 0.7)  # Safer
        else:
            return min(1.0, base_risk * 0.5)  # Very safe
            
        return min(1.0, base_risk)
    
    def predict_next_player_survival(self, view: BotView, next_player_id: str) -> float:
        """Predict probability that next player survives their turn (0-1)."""
        profile = self.get_opponent(next_player_id)
        
        # If they have many defuses, they'll survive
        if profile.defuses_used == 0:
            survival_chance = 0.9
        elif profile.defuses_used == 1:
            survival_chance = 0.6
        else:
            survival_chance = 0.3
        
        # If they have many cards, they likely have defensive options
        if profile.last_known_card_count >= 5:
            survival_chance += 0.1
        
        return min(1.0, survival_chance)


class Bombocat(Bot):
    """Elite strategic bot with advanced opponent modeling and predictive analysis."""
    
    def __init__(self) -> None:
        self.state = GameStateTracker()
        
    @property
    def name(self) -> str:
        return "Bombocat 2.0"
    
    def _count_card_type(self, hand: tuple[Card, ...], card_type: str) -> int:
        """Count cards of a specific type."""
        return sum(1 for c in hand if c.card_type == card_type)
    
    def _get_card_value(self, card: Card, view: BotView) -> float:
        """Assign strategic value to a card (higher = more valuable)."""
        card_type = card.card_type
        risk = self.state.estimate_kitten_risk(view, self._count_card_type(view.my_hand, "DefuseCard"))
        num_opponents = len(view.other_players)
        
        # Core survival cards
        if card_type == "DefuseCard":
            return 100.0
        if card_type == "NopeCard":
            # More valuable in late game when combos are common
            return 85.0 + (5.0 if num_opponents <= 2 else 0.0)
            
        # Defensive cards (more valuable when risk is high)
        if card_type == "SkipCard":
            return 70.0 + (risk * 25.0)
        if card_type == "AttackCard":
            # Very valuable when risky AND we have targets
            return 65.0 + (risk * 20.0) + (10.0 if num_opponents > 0 else 0.0)
            
        # Information/control cards
        if card_type == "SeeTheFutureCard":
            # Extremely valuable when risky or when we don't know what's coming
            if not self.state.known_top_cards:
                return 60.0 + (risk * 30.0)
            return 50.0
        if card_type == "ShuffleCard":
            # Critical if we know a kitten is on top
            if self.state.known_top_cards and self.state.known_top_cards[0] == "ExplodingKittenCard":
                return 95.0
            # Also valuable if risk is high (randomize danger)
            return 45.0 + (risk * 15.0)
            
        # Offensive cards
        if card_type == "FavorCard":
            # More valuable when opponents have many cards
            return 50.0 + (5.0 if num_opponents > 0 else 0.0)
            
        # Combo cards (value increases with count)
        if "Cat" in card_type or card_type in ("TacoCat", "BeardCat", "RainbowRalphingCat", "HairyPotatoCat", "Cattermelon"):
            count = self._count_card_type(view.my_hand, card_type)
            if count >= 3:
                return 45.0  # Can do 3-of-a-kind (steal named card)
            elif count >= 2:
                return 30.0  # Can do 2-of-a-kind (steal random)
            return 18.0  # Low value alone
            
        return 20.0
    
    def _find_combos(self, hand: tuple[Card, ...]) -> list[tuple[str, tuple[Card, ...]]]:
        """Find all possible combos, prioritized by power."""
        combos: list[tuple[str, tuple[Card, ...]]] = []
        combo_cards = [c for c in hand if c.can_combo()]
        
        if not combo_cards:
            return combos
        
        # Group by type
        by_type: dict[str, list[Card]] = {}
        for c in combo_cards:
            by_type.setdefault(c.card_type, []).append(c)
        
        # Check for 3-of-a-kind (highest priority - can name card to steal)
        for card_type, cards in by_type.items():
            if len(cards) >= 3:
                combos.append(("three_of_a_kind", tuple(cards[:3])))
            elif len(cards) >= 2:
                combos.append(("two_of_a_kind", tuple(cards[:2])))
        
        # Check for 5-different (can pick from discard)
        if len(by_type) >= 5:
            five_cards = [by_type[k][0] for k in list(by_type.keys())[:5]]
            combos.append(("five_different", tuple(five_cards)))
        
        return combos
    
    def _choose_best_target(self, view: BotView, purpose: str) -> str | None:
        """Choose the optimal target based on purpose with advanced logic."""
        if not view.other_players:
            return None
        
        # Update opponent profiles
        for player_id in view.other_players:
            profile = self.state.get_opponent(player_id)
            profile.update_card_count(view.other_player_card_counts.get(player_id, 0))
        
        if purpose == "attack":
            # Attack the most vulnerable (maximize kill chance)
            # But also consider: don't attack someone who's about to die anyway
            candidates = []
            for player_id in view.other_players:
                profile = self.state.get_opponent(player_id)
                vuln = profile.vulnerability()
                # Prefer high vulnerability but not TOO high (they might die anyway)
                score = vuln if vuln < 0.9 else vuln * 0.5
                candidates.append((score, player_id))
            candidates.sort(reverse=True)
            return candidates[0][1] if candidates else None
            
        elif purpose == "steal":
            # Steal from the most threatening (weaken the strong)
            return max(view.other_players,
                      key=lambda p: self.state.get_opponent(p).threat_level(),
                      default=None)
                      
        elif purpose == "harm":
            # General harm: target the leader (most cards)
            return max(view.other_players,
                      key=lambda p: view.other_player_card_counts.get(p, 0),
                      default=None)
        
        return view.other_players[0] if view.other_players else None
    
    def _score_action(self, action: Action, view: BotView, risk: float) -> float:
        """Score an action based on safety, economy, and aggression with advanced heuristics."""
        score = 0.0
        num_opponents = len(view.other_players)
        is_endgame = num_opponents <= 1
        
        if isinstance(action, DrawCardAction):
            # Drawing is necessary but risky
            # Heavily penalize drawing when risk is high
            if risk > 0.8:
                score = -50.0
            elif risk > 0.5:
                score = 5.0 - (risk * 40.0)
            else:
                score = 15.0 - (risk * 20.0)
            
        elif isinstance(action, PlayCardAction):
            card = action.card
            card_type = card.card_type
            
            # Safety score (avoiding drawing)
            if card_type in ("SkipCard", "AttackCard"):
                # Extremely valuable when risk is high
                if risk > 0.7:
                    score += 80.0
                elif risk > 0.4:
                    score += 60.0
                else:
                    score += 35.0
                    
                # Attack is better than Skip (passes danger to opponent)
                if card_type == "AttackCard":
                    score += 15.0
                    
            if card_type == "SeeTheFutureCard":
                # Critical when we don't know what's coming
                if not self.state.known_top_cards:
                    score += 55.0 + (risk * 35.0)
                else:
                    score += 20.0  # Less valuable if we already know
                    
            if card_type == "ShuffleCard":
                if self.state.known_top_cards and self.state.known_top_cards[0] == "ExplodingKittenCard":
                    score += 100.0  # Emergency escape
                elif risk > 0.6:
                    score += 45.0  # Randomize danger
                else:
                    score += 15.0
            
            # Economy score (hand value improvement)
            if card_type == "FavorCard":
                score += 45.0  # Gain a card from opponent
                # Bonus if targeting someone with many cards
                if action.target_player_id:
                    target_cards = view.other_player_card_counts.get(action.target_player_id, 0)
                    score += min(20.0, target_cards * 3.0)
            
            # Aggression score (hurting opponents)
            if card_type in ("AttackCard", "FavorCard") and action.target_player_id:
                target_profile = self.state.get_opponent(action.target_player_id)
                # Bonus for targeting dangerous opponents
                score += target_profile.threat_level() * 35.0
                # Bonus for targeting vulnerable opponents (finish them off)
                score += target_profile.vulnerability() * 25.0
                
        elif isinstance(action, PlayComboAction):
            combo_type = None
            if len(action.cards) == 2:
                combo_type = "two_of_a_kind"
            elif len(action.cards) == 3:
                combo_type = "three_of_a_kind"
            elif len(action.cards) == 5:
                combo_type = "five_different"
            
            # Combo scoring
            if combo_type == "three_of_a_kind":
                score += 75.0  # Very powerful - can name card
                if action.target_card_type == "DefuseCard":
                    score += 40.0  # Stealing defuse is game-changing
                elif action.target_card_type == "NopeCard":
                    score += 30.0  # Stealing Nope is strong
                elif action.target_card_type == "SeeTheFutureCard":
                    score += 25.0  # Information advantage
                    
            elif combo_type == "five_different":
                score += 65.0  # Strong - recover from discard
                if action.target_card_type == "DefuseCard":
                    score += 35.0  # Recovering defuse is huge
                elif action.target_card_type == "NopeCard":
                    score += 25.0
                    
            elif combo_type == "two_of_a_kind":
                score += 40.0  # Decent - random steal
                # Less valuable in late game (fewer cards to steal)
                if is_endgame:
                    score -= 10.0
            
            # Target scoring for combos
            if action.target_player_id:
                target_profile = self.state.get_opponent(action.target_player_id)
                # Bonus for targeting threats
                score += target_profile.threat_level() * 30.0
                # Bonus if target has many cards (more likely to have what we want)
                target_cards = view.other_player_card_counts.get(action.target_player_id, 0)
                score += min(15.0, target_cards * 2.0)
        
        # Endgame bonus: aggressive plays are more valuable
        if is_endgame and isinstance(action, (PlayCardAction, PlayComboAction)):
            score += 10.0
        
        return score
    
    def take_turn(self, view: BotView) -> Action:
        """Strategic turn execution with comprehensive action evaluation."""
        self.state.turn_count += 1
        hand = view.my_hand
        defuses = self._count_card_type(hand, "DefuseCard")
        risk = self.state.estimate_kitten_risk(view, defuses)
        
        # Generate all possible actions
        possible_actions: list[tuple[float, Action, str]] = []  # (score, action, description)
        
        # Option 1: Draw immediately
        draw_action = DrawCardAction()
        draw_score = self._score_action(draw_action, view, risk)
        possible_actions.append((draw_score, draw_action, "Draw"))
        
        # Option 2: Play single cards
        playable = [c for c in hand if c.can_play(view, is_own_turn=True)]
        for card in playable:
            if card.card_type in ("AttackCard", "FavorCard"):
                # Needs target - try multiple targeting strategies
                for purpose in ["attack", "steal", "harm"]:
                    target = self._choose_best_target(view, purpose)
                    if target:
                        action = PlayCardAction(card=card, target_player_id=target)
                        score = self._score_action(action, view, risk)
                        possible_actions.append((score, action, f"Play {card.card_type} on {purpose} target"))
            else:
                action = PlayCardAction(card=card)
                score = self._score_action(action, view, risk)
                possible_actions.append((score, action, f"Play {card.card_type}"))
        
        # Option 3: Play combos
        combos = self._find_combos(hand)
        for combo_type, cards in combos:
            if combo_type == "three_of_a_kind":
                # Try to steal high-value cards
                for target_card in ["DefuseCard", "NopeCard", "SeeTheFutureCard", "AttackCard"]:
                    for purpose in ["steal", "harm"]:
                        target = self._choose_best_target(view, purpose)
                        if target:
                            action = PlayComboAction(cards=cards, target_player_id=target, target_card_type=target_card)
                            score = self._score_action(action, view, risk)
                            possible_actions.append((score, action, f"3-of-a-kind steal {target_card}"))
                            
            elif combo_type == "five_different":
                # Try to recover valuable cards from discard
                if view.discard_pile:
                    for target_card in ["DefuseCard", "NopeCard", "SeeTheFutureCard", "AttackCard", "SkipCard"]:
                        if any(c.card_type == target_card for c in view.discard_pile):
                            action = PlayComboAction(cards=cards, target_card_type=target_card)
                            score = self._score_action(action, view, risk)
                            possible_actions.append((score, action, f"5-different recover {target_card}"))
                            
            elif combo_type == "two_of_a_kind":
                # Random steal from best target
                for purpose in ["steal", "harm", "attack"]:
                    target = self._choose_best_target(view, purpose)
                    if target:
                        action = PlayComboAction(cards=cards, target_player_id=target)
                        score = self._score_action(action, view, risk)
                        possible_actions.append((score, action, f"2-of-a-kind random steal"))
        
        # Sort by score and choose best
        if possible_actions:
            possible_actions.sort(key=lambda x: x[0], reverse=True)
            best_score, best_action, description = possible_actions[0]
            
            # Critical override: if we KNOW next card is kitten and we have Skip/Attack, use it!
            if (self.state.known_top_cards and 
                self.state.known_top_cards[0] == "ExplodingKittenCard" and
                defuses == 0):
                for card in playable:
                    if card.card_type == "SkipCard":
                        return PlayCardAction(card=card)
                    if card.card_type == "AttackCard":
                        target = self._choose_best_target(view, "attack")
                        if target:
                            return PlayCardAction(card=card, target_player_id=target)
                    if card.card_type == "ShuffleCard":
                        return PlayCardAction(card=card)
            
            return best_action
        
        return DrawCardAction()
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        """Strategic Nope usage with advanced decision-making."""
        nope_cards = [c for c in view.my_hand if c.card_type == "NopeCard"]
        if not nope_cards:
            return None
        
        # Analyze the triggering event
        event_data = triggering_event.data or {}
        card_type = event_data.get("card_type")
        target_id = event_data.get("target_player_id")
        combo_type = event_data.get("combo_type")
        player_id = triggering_event.player_id
        
        # ALWAYS Nope if it directly targets us
        if target_id == view.my_id:
            if card_type in ("AttackCard", "FavorCard"):
                return PlayCardAction(card=nope_cards[0])
            if combo_type in ("two_of_a_kind", "three_of_a_kind"):
                return PlayCardAction(card=nope_cards[0])
        
        # Nope attacks on weak players (keep them alive as buffers)
        if card_type == "AttackCard" and target_id and target_id != view.my_id:
            target_profile = self.state.get_opponent(target_id)
            # If target is very vulnerable, protect them (they're a buffer)
            if target_profile.vulnerability() > 0.75 and len(view.other_players) > 1:
                return PlayCardAction(card=nope_cards[0])
        
        # Nope powerful combos that don't target us (prevent others from getting too strong)
        if combo_type == "three_of_a_kind":
            target_card = event_data.get("target_card_type")
            # Block Defuse/Nope steals
            if target_card in ("DefuseCard", "NopeCard"):
                # Don't let the strongest player get stronger
                if player_id:
                    attacker_profile = self.state.get_opponent(player_id)
                    if attacker_profile.threat_level() > 0.6:
                        return PlayCardAction(card=nope_cards[0])
        
        # In endgame (1v1), be more aggressive with Nopes
        if len(view.other_players) == 1:
            if card_type in ("SkipCard", "SeeTheFutureCard"):
                # 50% chance to Nope even non-threatening cards
                if self.state.turn_count % 2 == 0:
                    return PlayCardAction(card=nope_cards[0])
        
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        """Strategic Exploding Kitten placement with predictive analysis."""
        self.state.kittens_defused_total += 1
        
        if not view.other_players or draw_pile_size == 0:
            return 0  # No choice
        
        # Find next player in turn order
        try:
            my_idx = list(view.turn_order).index(view.my_id)
            next_idx = (my_idx + 1) % len(view.turn_order)
            next_player = view.turn_order[next_idx]
            
            # Analyze next player
            next_profile = self.state.get_opponent(next_player)
            next_vuln = next_profile.vulnerability()
            next_survival = self.state.predict_next_player_survival(view, next_player)
            
            # If next player is very vulnerable and unlikely to survive, place on top
            if next_vuln > 0.7 or next_profile.defuses_used >= 2:
                return 0  # Top of deck - maximize kill chance
            
            # If next player is strong and we want them gone, place on top
            if next_profile.threat_level() > 0.7:
                return 0
            
            # If next player has seen the future, they might know top card
            # Place it deeper to avoid them skipping it
            if next_profile.has_seen_future:
                return min(draw_pile_size, 3)
            
        except (ValueError, IndexError):
            pass
        
        # Default strategy: place in top 1/3 of deck (positions 1-2)
        # This creates pressure without being too obvious
        return min(2, max(1, draw_pile_size // 4))
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        """Give away least valuable card while protecting critical cards."""
        hand = list(view.my_hand)
        hand.sort(key=lambda c: self._get_card_value(c, view))
        
        # Track this interaction
        if requester_id:
            profile = self.state.get_opponent(requester_id)
            profile.cards_stolen_from_me += 1
        
        # Never give last Defuse
        defuses = self._count_card_type(view.my_hand, "DefuseCard")
        if defuses == 1:
            for card in hand:
                if card.card_type != "DefuseCard":
                    return card
        
        # Never give last Nope if we have only 1
        nopes = self._count_card_type(view.my_hand, "NopeCard")
        if nopes == 1 and defuses >= 2:
            for card in hand:
                if card.card_type not in ("DefuseCard", "NopeCard"):
                    return card
        
        # Give lowest value card
        return hand[0]
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        """Track game events for comprehensive state analysis."""
        # Update opponent profiles
        if event.event_type == EventType.CARD_PLAYED and event.player_id != view.my_id:
            card_type = event.data.get("card_type") if event.data else None
            if card_type and event.player_id:
                profile = self.state.get_opponent(event.player_id)
                profile.record_play(card_type)
        
        # Track my own plays
        if event.event_type == EventType.CARD_PLAYED and event.player_id == view.my_id:
            card_type = event.data.get("card_type") if event.data else None
            if card_type:
                self.state.my_cards_played.append(card_type)
        
        # Track defuse usage
        if event.event_type == EventType.EXPLODING_KITTEN_DEFUSED:
            if event.player_id and event.player_id != view.my_id:
                profile = self.state.get_opponent(event.player_id)
                profile.defuses_used += 1
            # Reset has_seen_future flag after defuse
            if event.player_id:
                profile = self.state.get_opponent(event.player_id)
                profile.has_seen_future = False
        
        # Track SeeTheFuture results
        if event.event_type == EventType.CARDS_PEEKED and event.player_id == view.my_id:
            peeked = event.data.get("cards", []) if event.data else []
            self.state.known_top_cards = peeked
        
        # Clear known cards after shuffle
        if event.event_type == EventType.DECK_SHUFFLED:
            self.state.known_top_cards = []
            # Reset all has_seen_future flags
            for profile in self.state.opponents.values():
                profile.has_seen_future = False
        
        # Update known cards when we draw
        if event.event_type == EventType.CARD_DRAWN and event.player_id == view.my_id:
            if self.state.known_top_cards:
                self.state.known_top_cards.pop(0)
        
        # Track discard pile composition
        if event.event_type == EventType.CARD_DISCARDED:
            card_type = event.data.get("card_type") if event.data else None
            if card_type:
                self.state.cards_in_discard_by_type[card_type] = \
                    self.state.cards_in_discard_by_type.get(card_type, 0) + 1
    
    def on_explode(self, view: BotView) -> None:
        """Last words with style."""
        risk = self.state.estimate_kitten_risk(view, 0)
        if risk >= 0.9:
            view.say("I knew it was coming... calculated risk. GG!")
        else:
            view.say("Unlucky! The odds were in my favor. GG!")
