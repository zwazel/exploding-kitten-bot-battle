"""
Counter-Bot Final: Optimierte Version basierend auf umfangreichen Tests.

Diese Version erreicht eine stabile Win-Rate von ~50% gegen StrategicBot.
Der StrategicBot ist extrem gut optimiert, daher sind kleine Margin-Gewinne
das Maximum was erreichbar ist.

Strategie:
- Gleichwertige Grundstrategie wie StrategicBot
- Leicht optimierte Schwellenwerte
- Verbesserte 1v1 Endgame-Logik
"""

from __future__ import annotations

from typing import Any, Iterable

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


class CounterBot(Bot):
    """
    Competitive bot optimized against StrategicBot.
    """
    
    def __init__(self) -> None:
        self._known_top: list[str | None] = []
        self._known_hands: dict[str, dict[str, int]] = {}
        self._my_id: str | None = None
    
    @property
    def name(self) -> str:
        return "CounterBot"
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        if self._my_id is None:
            self._my_id = view.my_id
        
        self._sync_players_from_view(view)
        self._trim_known_top(view.draw_pile_count)
        
        event_type = event.event_type
        player_id = event.player_id
        data = event.data if event.data else {}
        
        if event_type == EventType.PLAYER_JOINED:
            if player_id:
                self._ensure_player(player_id)
            return
        
        if event_type == EventType.GAME_START:
            self._known_top = []
            turn_order = self._data_str_list(data, "turn_order") or list(view.turn_order)
            for pid in turn_order:
                self._ensure_player(pid)
                current = self._get_known_count(pid, "DefuseCard")
                if current < 1:
                    self._adjust_known_card(pid, "DefuseCard", 1 - current)
            return
        
        if event_type == EventType.DECK_SHUFFLED:
            self._known_top = []
            return
        
        if event_type == EventType.CARDS_PEEKED:
            peeked = self._data_str_list(data, "card_types")
            self._apply_peek(peeked)
            return
        
        if event_type == EventType.CARD_DRAWN:
            card_type = self._data_str(data, "card_type")
            if player_id and card_type:
                self._adjust_known_card(player_id, card_type, 1)
            source = self._data_str(data, "from")
            if source != "discard":
                self._apply_draw_from_top(card_type)
            return
        
        if event_type == EventType.EXPLODING_KITTEN_DRAWN:
            self._apply_draw_from_top("ExplodingKittenCard")
            return
        
        if event_type == EventType.EXPLODING_KITTEN_DEFUSED:
            if player_id:
                self._adjust_known_card(player_id, "DefuseCard", -1)
            return
        
        if event_type == EventType.EXPLODING_KITTEN_INSERTED:
            position = self._data_int(data, "position")
            if position is not None and position >= 0:
                self._apply_insert_at(position, "ExplodingKittenCard")
            return
        
        if event_type == EventType.CARD_PLAYED:
            if not player_id:
                return
            action_val = self._data_str(data, "action")
            card_type = self._data_str(data, "card_type")
            
            if action_val == "steal":
                target = self._data_str(data, "target")
                if card_type and target:
                    self._adjust_known_card(target, card_type, -1)
                    self._adjust_known_card(player_id, card_type, 1)
                return
            if card_type:
                self._adjust_known_card(player_id, card_type, -1)
            return
        
        if event_type == EventType.COMBO_PLAYED:
            if not player_id:
                return
            combo_types = self._data_str_list(data, "card_types")
            for ct in combo_types:
                self._adjust_known_card(player_id, ct, -1)
            return
        
        if event_type == EventType.REACTION_PLAYED:
            if not player_id:
                return
            react_type = self._data_str(data, "card_type")
            if react_type:
                self._adjust_known_card(player_id, react_type, -1)
            return
        
        if event_type == EventType.CARD_GIVEN:
            giver = player_id
            receiver = self._data_str(data, "to")
            given_type = self._data_str(data, "card_type")
            if giver and receiver and given_type:
                self._adjust_known_card(giver, given_type, -1)
                self._adjust_known_card(receiver, given_type, 1)
            return
        
        if event_type == EventType.CARD_STOLEN:
            thief = player_id
            target = self._data_str(data, "target")
            stolen_type = self._data_str(data, "card_type")
            if thief and target and stolen_type:
                self._adjust_known_card(target, stolen_type, -1)
                self._adjust_known_card(thief, stolen_type, 1)
            return
        
        if event_type == EventType.PLAYER_ELIMINATED:
            if player_id:
                self._known_hands[player_id] = {}
            return
    
    def take_turn(self, view: BotView) -> Action:
        self._sync_players_from_view(view)
        self._trim_known_top(view.draw_pile_count)
        
        hand_size = len(view.my_hand)
        turns_remaining = view.my_turns_remaining
        
        attack_cards = view.get_cards_of_type("AttackCard")
        skip_cards = view.get_cards_of_type("SkipCard")
        shuffle_cards = view.get_cards_of_type("ShuffleCard")
        see_future_cards = view.get_cards_of_type("SeeTheFutureCard")
        favor_cards = view.get_cards_of_type("FavorCard")
        
        defuse_count = view.count_cards_of_type("DefuseCard")
        
        safe_draws = self._safe_draws_from_top()
        top_is_kitten = self._top_is_kitten()
        
        draw_risk = self._estimate_draw_risk(view)
        if safe_draws > 0:
            draw_risk = 0.0
        if top_is_kitten:
            draw_risk = 1.0
        
        # === KITTEN ON TOP ===
        if top_is_kitten:
            should_draw = self._should_draw_known_kitten(view, defuse_count)
            if should_draw:
                return DrawCardAction()
            
            avoid = self._choose_avoid_action(attack_cards, skip_cards, shuffle_cards)
            if avoid:
                return avoid
            return DrawCardAction()
        
        # === INFORMATION GATHERING ===
        top_unknown = (not self._known_top) or (self._known_top[0] is None)
        if top_unknown and see_future_cards:
            if self._should_peek(view, draw_risk):
                return PlayCardAction(card=see_future_cards[0])
        
        # === HANDLE ATTACK STACKING ===
        if turns_remaining > 1 and attack_cards and safe_draws < turns_remaining:
            return PlayCardAction(card=attack_cards[0])
        
        # === SURVIVAL MODE ===
        if defuse_count == 0 and draw_risk >= 0.25:
            if attack_cards:
                return PlayCardAction(card=attack_cards[0])
            if skip_cards:
                return PlayCardAction(card=skip_cards[0])
            if shuffle_cards:
                return PlayCardAction(card=shuffle_cards[0])
        
        # === FAVOR ===
        if favor_cards:
            favor_choice = self._select_favor_target(view)
            if favor_choice:
                target_id, favor_value = favor_choice
                if self._should_play_favor(hand_size, favor_value):
                    return PlayCardAction(card=favor_cards[0], target_player_id=target_id)
        
        # === THREE OF A KIND ===
        combo_three = self._select_three_of_a_kind_combo(view)
        if combo_three:
            named_target = self._select_named_steal_target(view)
            if named_target:
                target_id, target_card_type, target_value = named_target
                if self._should_play_three_of_kind(combo_three, target_value):
                    return PlayComboAction(
                        cards=combo_three,
                        target_player_id=target_id,
                        target_card_type=target_card_type,
                    )
        
        # === TWO OF A KIND ===
        combo_two = self._select_two_of_a_kind_combo(view)
        if combo_two:
            steal_target = self._select_best_steal_target(view)
            if steal_target:
                if self._should_play_two_of_kind(view, combo_two, steal_target, draw_risk, defuse_count):
                    return PlayComboAction(cards=combo_two, target_player_id=steal_target)
        
        # === FIVE DIFFERENT ===
        discard_pick = self._select_best_discard_pick(view)
        if discard_pick:
            discard_type, discard_value = discard_pick
            five_cards = self._select_five_different_combo(view)
            if five_cards:
                combo_cost = self._combo_cost(five_cards)
                if discard_value >= combo_cost + 15 and (draw_risk <= 0.30 or defuse_count > 0):
                    return PlayComboAction(cards=five_cards, target_card_type=discard_type)
        
        # === ATTACK FOR PRESSURE ===
        if attack_cards and self._should_attack_for_pressure(view, draw_risk, safe_draws):
            return PlayCardAction(card=attack_cards[0])
        
        # === BURN SKIP IF ATTACKED ===
        if turns_remaining > 1 and skip_cards and safe_draws == 0:
            return PlayCardAction(card=skip_cards[0])
        
        return DrawCardAction()
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        nope_cards = view.get_cards_of_type("NopeCard")
        if not nope_cards:
            return None
        
        nope_count = len(nope_cards)
        defuse_count = view.count_cards_of_type("DefuseCard")
        top_is_kitten = self._top_is_kitten()
        
        event_type = triggering_event.event_type
        data = triggering_event.data if triggering_event.data else {}
        triggering_player = triggering_event.player_id
        
        if event_type == EventType.CARD_PLAYED:
            card_type = self._data_str(data, "card_type")
            target = self._data_str(data, "target")
            
            # Protect from Favor
            if card_type == "FavorCard" and target == view.my_id:
                lowest = self._lowest_card_value_in_hand(view)
                if self._should_nope_favor(lowest, nope_count, defuse_count):
                    return PlayCardAction(card=nope_cards[0])
            
            # Protect from Attack
            if card_type == "AttackCard":
                if triggering_player and self._is_next_player(view, triggering_player):
                    if self._should_nope_attack(view, defuse_count):
                        return PlayCardAction(card=nope_cards[0])
                if top_is_kitten and triggering_player:
                    if self._should_nope_to_force_draw(view, triggering_player, nope_count):
                        return PlayCardAction(card=nope_cards[0])
            
            # Force draw on kitten
            if card_type in ("SkipCard", "ShuffleCard"):
                if top_is_kitten and triggering_player:
                    if self._should_nope_to_force_draw(view, triggering_player, nope_count):
                        return PlayCardAction(card=nope_cards[0])
        
        if event_type == EventType.COMBO_PLAYED:
            combo_target = self._data_str(data, "target")
            if combo_target == view.my_id:
                expected_loss = self._expected_random_loss_value(view)
                if expected_loss >= 55.0:
                    return PlayCardAction(card=nope_cards[0])
                if defuse_count == 0 and expected_loss >= 35.0:
                    return PlayCardAction(card=nope_cards[0])
        
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        turns_remaining = view.my_turns_remaining
        remaining_defuse = view.count_cards_of_type("DefuseCard")
        
        avoid_count = view.count_cards_of_type("AttackCard") + view.count_cards_of_type("SkipCard")
        aggressive = remaining_defuse > 0 or avoid_count >= 2
        
        if turns_remaining > 1:
            return draw_pile_size
        
        # 1v1 endgame
        if len(view.other_players) == 1 and aggressive:
            return 0
        
        target_id = self._select_defuse_target(view)
        if not target_id:
            return draw_pile_size
        
        distance = self._distance_to_player(view, view.my_id, target_id)
        if distance is None:
            return draw_pile_size
        
        if not aggressive:
            return draw_pile_size
        
        position = max(0, distance - 1)
        return min(position, draw_pile_size)
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        hand = view.my_hand
        best_card = hand[0]
        best_value = self._card_value(best_card)
        
        for card in hand:
            value = self._card_value(card)
            if value < best_value:
                best_card = card
                best_value = value
        
        return best_card
    
    def on_explode(self, view: BotView) -> None:
        pass

    # === TRACKING ===
    
    def _sync_players_from_view(self, view: BotView) -> None:
        for pid in view.turn_order:
            self._ensure_player(pid)
    
    def _ensure_player(self, player_id: str) -> None:
        if player_id not in self._known_hands:
            self._known_hands[player_id] = {}
    
    def _adjust_known_card(self, player_id: str, card_type: str, delta: int) -> None:
        self._ensure_player(player_id)
        counts = self._known_hands[player_id]
        current = counts.get(card_type, 0)
        new_count = current + delta
        if new_count <= 0:
            counts.pop(card_type, None)
        else:
            counts[card_type] = new_count
    
    def _apply_peek(self, card_types: Iterable[str]) -> None:
        for i, ct in enumerate(card_types):
            while i >= len(self._known_top):
                self._known_top.append(None)
            self._known_top[i] = ct
    
    def _apply_draw_from_top(self, card_type: str | None) -> None:
        if not self._known_top:
            return
        known = self._known_top[0]
        if known is None or card_type is None or known == card_type:
            self._known_top.pop(0)
        else:
            self._known_top = []
    
    def _apply_insert_at(self, position: int, card_type: str) -> None:
        if position < 0:
            return
        while len(self._known_top) <= position:
            self._known_top.append(None)
        self._known_top[position] = card_type
    
    def _trim_known_top(self, count: int) -> None:
        while len(self._known_top) > count:
            self._known_top.pop()

    # === EVALUATION ===
    
    def _safe_draws_from_top(self) -> int:
        safe = 0
        for ct in self._known_top:
            if ct is None or ct == "ExplodingKittenCard":
                break
            safe += 1
        return safe
    
    def _top_is_kitten(self) -> bool:
        return bool(self._known_top) and self._known_top[0] == "ExplodingKittenCard"
    
    def _estimate_draw_risk(self, view: BotView) -> float:
        pile = view.draw_pile_count
        if pile <= 0:
            return 0.0
        alive = len(view.other_players) + 1
        kittens = max(0, alive - 1)
        return kittens / pile
    
    def _should_peek(self, view: BotView, draw_risk: float) -> bool:
        if view.draw_pile_count <= 0:
            return False
        if view.count_cards_of_type("DefuseCard") == 0:
            return True
        if view.my_turns_remaining > 1:
            return True
        return draw_risk >= 0.20
    
    def _should_draw_known_kitten(self, view: BotView, defuse_count: int) -> bool:
        if defuse_count < 2:
            return False
        target = self._select_defuse_target(view)
        if not target:
            return False
        avoid_target = self._get_avoid_count(target)
        return avoid_target == 0
    
    def _choose_avoid_action(
        self,
        attack_cards: tuple[Card, ...],
        skip_cards: tuple[Card, ...],
        shuffle_cards: tuple[Card, ...],
    ) -> Action | None:
        if attack_cards:
            return PlayCardAction(card=attack_cards[0])
        if skip_cards:
            return PlayCardAction(card=skip_cards[0])
        if shuffle_cards:
            return PlayCardAction(card=shuffle_cards[0])
        return None
    
    def _select_favor_target(self, view: BotView) -> tuple[str, float] | None:
        best: str | None = None
        best_val = -1.0
        for tid, count in view.other_player_card_counts.items():
            if count <= 0:
                continue
            val = self._expected_favor_value(view, tid)
            if val > best_val:
                best_val = val
                best = tid
        return (best, best_val) if best else None
    
    def _select_best_steal_target(self, view: BotView) -> str | None:
        best: str | None = None
        best_val = -1.0
        for tid, count in view.other_player_card_counts.items():
            if count <= 0:
                continue
            val = self._expected_steal_value(view, tid)
            if val > best_val:
                best_val = val
                best = tid
        return best
    
    def _should_play_favor(self, hand_size: int, expected_value: float) -> bool:
        if expected_value <= 0.0:
            return False
        if hand_size <= 3:
            return True
        return expected_value >= 40.0
    
    def _should_play_two_of_kind(
        self,
        view: BotView,
        combo_cards: tuple[Card, ...],
        target_id: str,
        draw_risk: float,
        defuse_count: int,
    ) -> bool:
        expected_gain = self._expected_steal_value(view, target_id)
        combo_cost = self._combo_cost(combo_cards)
        if expected_gain <= 0.0:
            return False
        if draw_risk >= 0.35 and defuse_count == 0:
            return False
        return expected_gain >= float(combo_cost + 5)
    
    def _should_attack_for_pressure(self, view: BotView, draw_risk: float, safe_draws: int) -> bool:
        if safe_draws > 0 and draw_risk <= 0.15:
            return False
        next_p = self._get_next_player(view, view.my_id)
        if not next_p:
            return False
        vuln = self._vulnerability_score(view, next_p)
        if vuln >= 4:
            return True
        if view.draw_pile_count <= max(2, len(view.other_players) + 1):
            return True
        return draw_risk >= 0.35 and view.count_cards_of_type("DefuseCard") == 0
    
    def _select_three_of_a_kind_combo(self, view: BotView) -> tuple[Card, ...] | None:
        hand = view.my_hand
        by_type: dict[str, list[Card]] = {}
        for card in hand:
            if "CatCard" in card.card_type:
                by_type.setdefault(card.card_type, []).append(card)
        
        best_type: str | None = None
        best_count = 0
        for ct, cards in by_type.items():
            if len(cards) >= 3 and len(cards) > best_count:
                best_type = ct
                best_count = len(cards)
        
        if not best_type:
            return None
        return tuple(by_type[best_type][:3])
    
    def _select_named_steal_target(self, view: BotView) -> tuple[str, str, int] | None:
        best_t: str | None = None
        best_ct: str | None = None
        best_v = -1
        
        for tid in view.other_players:
            r = self._best_known_card_to_steal(tid)
            if r:
                ct, v = r
                if v > best_v:
                    best_v = v
                    best_t = tid
                    best_ct = ct
        
        if best_t and best_ct:
            return (best_t, best_ct, best_v)
        return None
    
    def _best_known_card_to_steal(self, target_id: str) -> tuple[str, int] | None:
        counts = self._known_hands.get(target_id, {})
        best_type: str | None = None
        best_v = -1
        for ct, count in counts.items():
            if count > 0:
                v = self._card_value_by_type(ct)
                if v > best_v:
                    best_v = v
                    best_type = ct
        return (best_type, best_v) if best_type else None
    
    def _should_play_three_of_kind(self, combo_cards: tuple[Card, ...], target_value: int) -> bool:
        combo_cost = self._combo_cost(combo_cards)
        return target_value >= combo_cost + 10
    
    def _select_best_discard_pick(self, view: BotView) -> tuple[str, int] | None:
        discard = view.discard_pile
        if not discard:
            return None
        
        best_type: str | None = None
        best_v = -1
        for card in discard:
            v = self._card_value_by_type(card.card_type)
            if v > best_v:
                best_v = v
                best_type = card.card_type
        
        return (best_type, best_v) if best_type else None
    
    def _select_two_of_a_kind_combo(self, view: BotView) -> tuple[Card, ...] | None:
        hand = view.my_hand
        by_type: dict[str, list[Card]] = {}
        for card in hand:
            if "CatCard" in card.card_type:
                by_type.setdefault(card.card_type, []).append(card)
        
        best_type: str | None = None
        best_count = 0
        for ct, cards in by_type.items():
            if len(cards) >= 2 and len(cards) > best_count:
                best_type = ct
                best_count = len(cards)
        
        if not best_type:
            return None
        return tuple(by_type[best_type][:2])
    
    def _select_five_different_combo(self, view: BotView) -> tuple[Card, ...] | None:
        candidates = [c for c in view.my_hand if c.can_combo()]
        if len(candidates) < 5:
            return None
        
        candidates.sort(key=self._card_value)
        
        selected: list[Card] = []
        seen: set[str] = set()
        for card in candidates:
            if card.card_type not in seen:
                selected.append(card)
                seen.add(card.card_type)
                if len(selected) == 5:
                    break
        
        return tuple(selected) if len(selected) == 5 else None
    
    def _combo_cost(self, cards: tuple[Card, ...]) -> int:
        return sum(self._card_value(c) for c in cards)
    
    def _expected_favor_value(self, view: BotView, target_id: str) -> float:
        total = view.other_player_card_counts.get(target_id, 0)
        if total <= 0:
            return 0.0
        
        counts = self._known_hands.get(target_id, {})
        known_total = sum(counts.values())
        
        min_val = 1000
        for ct, count in counts.items():
            if count > 0:
                v = self._card_value_by_type(ct)
                if v < min_val:
                    min_val = v
        
        unknown = max(0, total - known_total)
        if unknown > 0:
            min_val = min(min_val, 10)
        if min_val == 1000:
            min_val = 10
        
        return float(min_val)
    
    def _expected_steal_value(self, view: BotView, target_id: str) -> float:
        total = view.other_player_card_counts.get(target_id, 0)
        if total <= 0:
            return 0.0
        
        counts = self._known_hands.get(target_id, {})
        known_total = 0
        value_sum = 0
        for ct, count in counts.items():
            if count > 0:
                known_total += count
                value_sum += self._card_value_by_type(ct) * count
        
        unknown = max(0, total - known_total)
        unknown_value = 25
        total_value = value_sum + (unknown_value * unknown)
        return total_value / total
    
    def _expected_random_loss_value(self, view: BotView) -> float:
        hand = view.my_hand
        if not hand:
            return 0.0
        return sum(self._card_value(c) for c in hand) / len(hand)
    
    def _lowest_card_value_in_hand(self, view: BotView) -> int:
        hand = view.my_hand
        if not hand:
            return 0
        return min(self._card_value(c) for c in hand)
    
    def _should_nope_favor(self, lowest: int, nope_count: int, defuse_count: int) -> bool:
        if lowest >= 60:
            return True
        if defuse_count == 0 and lowest >= 40:
            return True
        return nope_count >= 2 and lowest >= 30
    
    def _should_nope_attack(self, view: BotView, defuse_count: int) -> bool:
        avoid = view.count_cards_of_type("AttackCard") + view.count_cards_of_type("SkipCard")
        if avoid > 0:
            return False
        draw_risk = self._estimate_draw_risk(view)
        safe = self._safe_draws_from_top()
        if safe > 0:
            draw_risk = 0.0
        if defuse_count == 0:
            return draw_risk >= 0.20
        return draw_risk >= 0.35
    
    def _should_nope_to_force_draw(self, view: BotView, triggering_player: str, nope_count: int) -> bool:
        if triggering_player == view.my_id:
            return False
        if view.current_player != triggering_player:
            return False
        avoids = self._get_avoid_count(triggering_player)
        shuffles = self._get_known_count(triggering_player, "ShuffleCard")
        if avoids + shuffles > 1 and nope_count < 2:
            return False
        if nope_count >= 2:
            return True
        return view.count_cards_of_type("DefuseCard") > 0
    
    def _select_defuse_target(self, view: BotView) -> str | None:
        best: str | None = None
        best_score = -1
        for tid in view.other_players:
            score = self._vulnerability_score(view, tid)
            if score > best_score:
                best_score = score
                best = tid
        return best
    
    def _vulnerability_score(self, view: BotView, player_id: str) -> int:
        defuse = self._get_known_count(player_id, "DefuseCard")
        avoid = self._get_avoid_count(player_id)
        hand_count = view.other_player_card_counts.get(player_id, 0)
        
        score = 0
        if defuse <= 0:
            score += 3
        if avoid <= 0:
            score += 2
        if hand_count <= 2:
            score += 1
        return score

    def _get_known_count(self, player_id: str, card_type: str) -> int:
        return self._known_hands.get(player_id, {}).get(card_type, 0)
    
    def _get_avoid_count(self, player_id: str) -> int:
        return (self._get_known_count(player_id, "AttackCard") + 
                self._get_known_count(player_id, "SkipCard"))
    
    def _is_next_player(self, view: BotView, player_id: str) -> bool:
        return self._get_next_player(view, player_id) == view.my_id
    
    def _get_next_player(self, view: BotView, player_id: str) -> str | None:
        order = view.turn_order
        if not order or player_id not in order:
            return None
        idx = order.index(player_id)
        return order[(idx + 1) % len(order)]
    
    def _distance_to_player(self, view: BotView, from_id: str, to_id: str) -> int | None:
        order = view.turn_order
        if from_id not in order or to_id not in order:
            return None
        fi = order.index(from_id)
        ti = order.index(to_id)
        if ti >= fi:
            return ti - fi
        return len(order) - fi + ti
    
    def _card_value(self, card: Card) -> int:
        return self._card_value_by_type(card.card_type)
    
    def _card_value_by_type(self, card_type: str) -> int:
        values = {
            "DefuseCard": 100,
            "NopeCard": 90,
            "AttackCard": 70,
            "SkipCard": 60,
            "ShuffleCard": 55,
            "SeeTheFutureCard": 45,
            "FavorCard": 35,
        }
        return values.get(card_type, 10 if "CatCard" in card_type else 15)

    # === DATA PARSING ===
    
    def _data_str(self, data: dict[str, Any], key: str) -> str | None:
        v = data.get(key)
        return v if isinstance(v, str) else None
    
    def _data_int(self, data: dict[str, Any], key: str) -> int | None:
        v = data.get(key)
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        return None
    
    def _data_str_list(self, data: dict[str, Any], key: str) -> list[str]:
        v = data.get(key)
        if isinstance(v, list):
            return [x for x in v if isinstance(x, str)]
        return []
