"""
OVERLORD BOT v2.0 - Harvey Specter Edition (God-Tier)
"I don't play the odds, I play the man."

Strategy:
1. Strict Resource Hoarding (Deck > 12)
2. Shadow Placement (Defuse -> Index 3)
3. Defuse Depletion (Targeted 3-of-a-kind)
4. Checkmate Calculation (Force death via Attack stacks)
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

from game.bots.base import (
    Action,
    Bot,
    DrawCardAction,
    PlayCardAction,
    PlayComboAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.history import EventType, GameEvent


class OverlordBot(Bot):
    
    # Utility & Thresholds
    VAL_DEFUSE = 100.0
    COST_ATTACK = 25.0
    COST_SKIP = 20.0
    COST_STF = 10.0
    
    # The "Specter" Line: Don't play cards if deck is larger than this
    HOARDING_THRESHOLD = 12 
    
    def __init__(self) -> None:
        self._global_memory: Dict[str, Dict] = {}
        self._initial_player_count: int = 0
        self._players_eliminated: int = 0
        self._known_top_cards: List[str] = []
        self._last_stf_deck_size: int = 0

    @property
    def name(self) -> str:
        return "Overlord Specter"

    # =========================================================================
    # MEMORY & TRACKING
    # =========================================================================

    def _init_memory(self, player_ids: List[str]) -> None:
        for pid in player_ids:
            if pid not in self._global_memory:
                self._global_memory[pid] = {
                    'defuse_count': 1,       # Everyone starts with 1
                    'nope_count': 0,
                    'has_used_defuse': False,
                    'cards_played': []
                }

    def on_event(self, event: GameEvent, view: BotView) -> None:
        if event.event_type == EventType.BOT_CHAT: return

        # 1. Game Start / Init
        if event.event_type == EventType.GAME_START:
            self._initial_player_count = len(view.other_players) + 1
            all_players = list(view.other_players) + [view.my_id]
            self._init_memory(all_players)
        
        # 2. Track Eliminations
        elif event.event_type == EventType.PLAYER_ELIMINATED:
            self._players_eliminated += 1
            if event.player_id in self._global_memory:
                del self._global_memory[event.player_id]
        
        # 3. Track Defuse Usage (CRITICAL)
        elif event.event_type == EventType.EXPLODING_KITTEN_DEFUSED:
            pid = event.player_id
            if pid in self._global_memory:
                self._global_memory[pid]['defuse_count'] = max(0, self._global_memory[pid]['defuse_count'] - 1)
                self._global_memory[pid]['has_used_defuse'] = True
        
        # 4. Track Card Plays (Count Nopes/Defuses/Attacks)
        elif event.event_type in [EventType.CARD_PLAYED, EventType.REACTION_PLAYED]:
            pid = event.player_id
            c_type = event.data.get('card_type')
            if pid in self._global_memory and c_type:
                # Decrement counts if we are tracking them
                if c_type == 'NopeCard':
                    self._global_memory[pid]['nope_count'] = max(0, self._global_memory[pid].get('nope_count', 0) - 1)
                
                # General tracking
                self._global_memory[pid]['cards_played'].append(c_type)

        # 5. STF / Top Deck Knowledge
        if event.event_type in [EventType.DECK_SHUFFLED, EventType.EXPLODING_KITTEN_INSERTED]:
            self._known_top_cards = []
        elif event.event_type == EventType.CARDS_PEEKED and event.player_id == view.my_id:
            self._known_top_cards = event.data.get("card_types", [])
            self._last_stf_deck_size = view.draw_pile_count
        elif event.event_type == EventType.CARD_DRAWN:
            if self._known_top_cards:
                self._known_top_cards.pop(0)

    # =========================================================================
    # CORE LOGIC
    # =========================================================================

    def _calculate_risk(self, view: BotView) -> float:
        """Calculate the raw risk of drawing."""
        if self._known_top_cards:
            return 1.0 if self._known_top_cards[0] == "ExplodingKittenCard" else 0.0
        
        N = view.draw_pile_count
        if N == 0: return 0.0
        
        # EKs = (Initial Players - 1) - Eliminated
        ek_remaining = max(0, (self._initial_player_count - 1) - self._players_eliminated)
        return ek_remaining / N

    def take_turn(self, view: BotView) -> Action:
        # 0. Sync STF state
        if view.draw_pile_count != self._last_stf_deck_size:
            self._known_top_cards = []
            self._last_stf_deck_size = view.draw_pile_count

        # 1. EMERGENCY: Known Death
        # If we KNOW the top card is an EK, we must act.
        if self._known_top_cards and self._known_top_cards[0] == "ExplodingKittenCard":
            return self._handle_emergency(view)

        # 2. CHECKMATE: Can we win right now?
        kill_move = self._check_for_checkmate(view)
        if kill_move:
            view.say("This deposition is over.")
            return kill_move

        # 3. HOARDING: Build the War Chest
        # If deck is large and we don't know there's a bomb, just draw.
        if view.draw_pile_count > self.HOARDING_THRESHOLD:
            # Only exception: Steal a Defuse if we have 3-of-a-kind
            combo = self._check_defuse_theft(view)
            if combo: return combo
            return DrawCardAction()

        # 4. STANDARD PLAY: Manage Risk
        return self._handle_standard_play(view)

    # =========================================================================
    # SUB-HANDLERS
    # =========================================================================

    def _handle_emergency(self, view: BotView) -> Action:
        """Top card is EK. We must not draw."""
        attacks = view.get_cards_of_type("AttackCard")
        skips = view.get_cards_of_type("SkipCard")
        shuffles = view.get_cards_of_type("ShuffleCard")
        
        # Attack is best (pass the bomb)
        if attacks: return PlayCardAction(card=attacks[0])
        # Skip is second best
        if skips: return PlayCardAction(card=skips[0])
        # Shuffle is a hail mary
        if shuffles: 
            self._known_top_cards = []
            view.say("Rolling the dice.")
            return PlayCardAction(card=shuffles[0])
        
        # If no moves, we draw and Defuse (handled by engine)
        return DrawCardAction()

    def _check_for_checkmate(self, view: BotView) -> Optional[Action]:
        """If opponent is weak and we can force draws > their hand size, kill them."""
        attacks = view.get_cards_of_type("AttackCard")
        if not attacks or not view.other_players: return None
        
        next_player = self._get_next_player(view)
        if not next_player: return None
        
        hand_size = view.other_player_card_counts.get(next_player, 0)
        mem = self._global_memory.get(next_player, {})
        
        # If they have no Defuse (tracked) or hand is tiny
        is_defenseless = mem.get('defuse_count', 1) == 0 or hand_size < 2
        
        # If deck is small (high density of bombs) and they are defenseless
        if view.draw_pile_count < 10 and is_defenseless:
            return PlayCardAction(card=attacks[0])
            
        return None

    def _handle_standard_play(self, view: BotView) -> Action:
        """Mid/Late game logic."""
        risk = self._calculate_risk(view)
        
        attacks = view.get_cards_of_type("AttackCard")
        skips = view.get_cards_of_type("SkipCard")
        stfs = view.get_cards_of_type("SeeTheFutureCard")
        
        # 1. Always steal Defuses if possible
        combo = self._check_defuse_theft(view)
        if combo: return combo

        # 2. Use STF if risk is getting scary (>15%) and we are blind
        if not self._known_top_cards and stfs and risk > 0.15:
            return PlayCardAction(card=stfs[0])
            
        # 3. If Risk is high (>25%), use avoidance
        if risk > 0.25:
            if attacks: return PlayCardAction(card=attacks[0])
            if skips: return PlayCardAction(card=skips[0])
            
        return DrawCardAction()

    def _check_defuse_theft(self, view: BotView) -> Optional[Action]:
        """Only use 3-of-a-kind to steal Defuses."""
        hand = view.my_hand
        counts = {}
        for c in hand:
            if c.can_combo():
                counts[c.card_type] = counts.get(c.card_type, []) + [c]
                
        # Find 3-of-a-kind
        for c_type, cards in counts.items():
            if len(cards) >= 3:
                # Find target with confirmed Defuse
                candidates = [p for p in view.other_players if self._global_memory.get(p, {}).get('defuse_count', 0) > 0]
                target = None
                if candidates:
                     # Pick the one with the smallest hand (highest probability of success)
                    target = min(candidates, key=lambda p: view.other_player_card_counts.get(p, 0))
                elif view.other_players:
                    # Fallback: Richest player
                    target = max(view.other_players, key=lambda p: view.other_player_card_counts.get(p, 0))
                
                if target:
                    return PlayComboAction(cards=tuple(cards[:3]), target_player_id=target, target_card_type="DefuseCard")
        return None

    # =========================================================================
    # REACTION & PLACEMENT (THE SPECTER TOUCH)
    # =========================================================================

    def react(self, view: BotView, event: GameEvent) -> Optional[Action]:
        nopes = view.get_cards_of_type("NopeCard")
        if not nopes: return None
        
        # Only Nope if it saves our life or our Defuse
        data = event.data or {}
        
        # 1. They are attacking US
        if event.event_type == EventType.CARD_PLAYED and data.get('card_type') == 'AttackCard':
            if self._is_next_player(view, event.player_id):
                view.say("I don't think so.")
                return PlayCardAction(card=nopes[0])

        # 2. They are stealing OUR Defuse
        if event.event_type == EventType.COMBO_PLAYED:
            if data.get('target_player_id') == view.my_id and data.get('target_card_type') == 'DefuseCard':
                view.say("You're looking at a cliff.")
                return PlayCardAction(card=nopes[0])
                
        return None

    def choose_defuse_position(self, view: BotView, pile_size: int) -> int:
        """
        The Shadow Placement.
        - Index 0: KILL. Use if next player is weak.
        - Index 3: SHADOW. Use to bypass 'See the Future'.
        """
        next_player = self._get_next_player(view)
        if next_player:
            mem = self._global_memory.get(next_player, {})
            hand_size = view.other_player_card_counts.get(next_player, 0)
            
            # KILL MODE: If they have no Defuse or <3 cards, top deck it.
            if mem.get('defuse_count', 1) == 0 or hand_size < 3:
                view.say("Bye.")
                return 0
        
        # SHADOW MODE: Place it 4th from top (Index 3).
        # Standard STF sees indices 0, 1, 2. This hides it just below their vision.
        return min(3, pile_size)

    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        # Give Shuffles or single Cats (useless cards)
        hand = sorted(view.my_hand, key=lambda c: 0 if c.card_type == "ShuffleCard" else 100)
        return hand[0]

    def _get_next_player(self, view: BotView) -> Optional[str]:
        if not view.turn_order or view.my_id not in view.turn_order: return None
        my_idx = view.turn_order.index(view.my_id)
        return view.turn_order[(my_idx + 1) % len(view.turn_order)]
        
    def _is_next_player(self, view: BotView, current_player: str) -> bool:
        nxt = self._get_next_player(view)
        return nxt == view.my_id if nxt else False
    
    def on_explode(self, view: BotView) -> None:
        pass
