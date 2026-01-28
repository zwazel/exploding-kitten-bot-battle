"""
Strategic bot with safety-first heuristics and public-state tracking.
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


class StrategicBot(Bot):
    """
    A deterministic bot that tracks public events and prioritizes survival.
    
    Strategy highlights:
    - Track known deck order slices from peeks and defuse insertions.
    - Track public hand composition for all players via events.
    - Avoid known Exploding Kittens and pressure vulnerable players.
    - Value actions using expected gains and defensive reserves.
    """
    
    def __init__(self) -> None:
        self._known_top: list[str | None] = []
        self._known_hands: dict[str, dict[str, int]] = dict[str, dict[str, int]]()
        self._my_id: str | None = None
    
    @property
    def name(self) -> str:
        return "StrategicBot"
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        if self._my_id is None:
            self._my_id = view.my_id
        
        self._sync_players_from_view(view)
        self._trim_known_top(view.draw_pile_count)
        
        event_type: EventType = event.event_type
        player_id: str | None = event.player_id
        data: dict[str, Any] = event.data if event.data else dict[str, Any]()
        
        if event_type == EventType.PLAYER_JOINED:
            if player_id is not None:
                self._ensure_player(player_id)
            return
        
        if event_type == EventType.GAME_START:
            self._known_top = []
            turn_order_list: list[str] = self._data_str_list(data, "turn_order")
            turn_order: Iterable[str] = turn_order_list if turn_order_list else view.turn_order
            pid: str
            for pid in turn_order:
                self._ensure_player(pid)
                current_defuse: int = self._get_known_count(pid, "DefuseCard")
                if current_defuse < 1:
                    self._adjust_known_card(pid, "DefuseCard", 1 - current_defuse)
            return
        
        if event_type == EventType.DECK_SHUFFLED:
            self._known_top = []
            return
        
        if event_type == EventType.CARDS_PEEKED:
            peeked_types: list[str] = self._data_str_list(data, "card_types")
            self._apply_peek(peeked_types)
            return
        
        if event_type == EventType.CARD_DRAWN:
            card_type_drawn: str | None = self._data_str(data, "card_type")
            if player_id is not None and card_type_drawn is not None:
                self._adjust_known_card(player_id, card_type_drawn, 1)
            source: str | None = self._data_str(data, "from")
            if source != "discard":
                self._apply_draw_from_top(card_type_drawn)
            return
        
        if event_type == EventType.EXPLODING_KITTEN_DRAWN:
            self._apply_draw_from_top("ExplodingKittenCard")
            return
        
        if event_type == EventType.EXPLODING_KITTEN_DEFUSED:
            if player_id is not None:
                self._adjust_known_card(player_id, "DefuseCard", -1)
            return
        
        if event_type == EventType.EXPLODING_KITTEN_INSERTED:
            position_value: int | None = self._data_int(data, "position")
            if position_value is not None and position_value >= 0:
                self._apply_insert_at(position_value, "ExplodingKittenCard")
            return
        
        if event_type == EventType.CARD_PLAYED:
            if player_id is None:
                return
            action_value: str | None = self._data_str(data, "action")
            card_type_value: str | None = self._data_str(data, "card_type")
            if action_value == "steal":
                target_id: str | None = self._data_str(data, "target")
                if card_type_value is not None and target_id is not None:
                    self._adjust_known_card(target_id, card_type_value, -1)
                    self._adjust_known_card(player_id, card_type_value, 1)
                return
            if card_type_value is not None:
                self._adjust_known_card(player_id, card_type_value, -1)
            return
        
        if event_type == EventType.COMBO_PLAYED:
            if player_id is None:
                return
            combo_types: list[str] = self._data_str_list(data, "card_types")
            combo_type: str
            for combo_type in combo_types:
                self._adjust_known_card(player_id, combo_type, -1)
            return
        
        if event_type == EventType.REACTION_PLAYED:
            if player_id is None:
                return
            reaction_card_type: str | None = self._data_str(data, "card_type")
            if reaction_card_type is not None:
                self._adjust_known_card(player_id, reaction_card_type, -1)
            return
        
        if event_type == EventType.CARD_GIVEN:
            giver_id: str | None = player_id
            receiver_id: str | None = self._data_str(data, "to")
            given_card_type: str | None = self._data_str(data, "card_type")
            if giver_id is not None and receiver_id is not None and given_card_type is not None:
                self._adjust_known_card(giver_id, given_card_type, -1)
                self._adjust_known_card(receiver_id, given_card_type, 1)
            return
        
        if event_type == EventType.CARD_STOLEN:
            thief_id: str | None = player_id
            target_id: str | None = self._data_str(data, "target")
            stolen_card_type: str | None = self._data_str(data, "card_type")
            if thief_id is not None and target_id is not None and stolen_card_type is not None:
                self._adjust_known_card(target_id, stolen_card_type, -1)
                self._adjust_known_card(thief_id, stolen_card_type, 1)
            return
        
        if event_type == EventType.PLAYER_ELIMINATED:
            if player_id is not None:
                self._known_hands[player_id] = dict[str, int]()
            return
    
    def take_turn(self, view: BotView) -> Action:
        self._sync_players_from_view(view)
        self._trim_known_top(view.draw_pile_count)
        
        hand_size: int = len(view.my_hand)
        turns_remaining: int = view.my_turns_remaining
        
        attack_cards: tuple[Card, ...] = view.get_cards_of_type("AttackCard")
        skip_cards: tuple[Card, ...] = view.get_cards_of_type("SkipCard")
        shuffle_cards: tuple[Card, ...] = view.get_cards_of_type("ShuffleCard")
        see_future_cards: tuple[Card, ...] = view.get_cards_of_type("SeeTheFutureCard")
        favor_cards: tuple[Card, ...] = view.get_cards_of_type("FavorCard")
        
        defuse_count: int = view.count_cards_of_type("DefuseCard")
        
        safe_draws: int = self._safe_draws_from_top()
        top_is_kitten: bool = self._top_is_kitten()
        
        draw_risk: float = self._estimate_draw_risk(view)
        if safe_draws > 0:
            draw_risk = 0.0
        if top_is_kitten:
            draw_risk = 1.0
        
        # Known kitten at the top: avoid drawing if possible.
        if top_is_kitten:
            should_draw_known: bool = self._should_draw_known_kitten(view, defuse_count)
            if should_draw_known:
                return DrawCardAction()
            avoid_action: Action | None = self._choose_avoid_action_for_kitten(
                attack_cards, skip_cards, shuffle_cards
            )
            if avoid_action is not None:
                return avoid_action
            return DrawCardAction()
        
        # Seek information if the top card is unknown and risk is meaningful.
        top_unknown: bool = (not self._known_top) or (self._known_top[0] is None)
        if top_unknown and see_future_cards:
            if self._should_peek(view, draw_risk):
                return PlayCardAction(card=see_future_cards[0])
        
        # If attacked and unsafe, transfer stacked turns with Attack.
        if turns_remaining > 1 and attack_cards and safe_draws < turns_remaining:
            return PlayCardAction(card=attack_cards[0])
        
        # High-risk turn without Defuse: avoid drawing if possible.
        if defuse_count == 0 and draw_risk >= 0.25:
            if attack_cards:
                return PlayCardAction(card=attack_cards[0])
            if skip_cards:
                return PlayCardAction(card=skip_cards[0])
            if shuffle_cards:
                return PlayCardAction(card=shuffle_cards[0])
        
        # Favor: take a card if the expected value is strong.
        if favor_cards:
            favor_choice: tuple[str, float] | None = self._select_favor_target(view)
            if favor_choice is not None:
                favor_target: str = favor_choice[0]
                favor_value: float = favor_choice[1]
                if self._should_play_favor(hand_size, favor_value):
                    return PlayCardAction(card=favor_cards[0], target_player_id=favor_target)
        
        # Three-of-a-kind combo: name and steal a specific card when we know it's held.
        combo_three: tuple[Card, ...] | None = self._select_three_of_a_kind_combo(view)
        if combo_three is not None:
            named_target: tuple[str, str, int] | None = self._select_named_steal_target(view)
            if named_target is not None:
                target_id: str = named_target[0]
                target_card_type: str = named_target[1]
                target_value: int = named_target[2]
                if self._should_play_three_of_kind(combo_three, target_value):
                    return PlayComboAction(
                        cards=combo_three,
                        target_player_id=target_id,
                        target_card_type=target_card_type,
                    )
        
        # Two-of-a-kind combo: steal if expected gain exceeds cost.
        combo_two: tuple[Card, ...] | None = self._select_two_of_a_kind_combo(view)
        if combo_two is not None:
            steal_target: str | None = self._select_best_steal_target(view)
            if steal_target is not None:
                if self._should_play_two_of_kind(view, combo_two, steal_target, draw_risk, defuse_count):
                    return PlayComboAction(cards=combo_two, target_player_id=steal_target)
        
        # Five-different combo: pick the best available discard when worth the cost.
        discard_pick: tuple[str, int] | None = self._select_best_discard_pick(view)
        if discard_pick is not None:
            discard_type: str = discard_pick[0]
            discard_value: int = discard_pick[1]
            five_cards: tuple[Card, ...] | None = self._select_five_different_combo(view)
            if five_cards is not None:
                combo_cost: int = self._combo_cost(five_cards)
                if discard_value >= combo_cost + 15 and (draw_risk <= 0.30 or defuse_count > 0):
                    return PlayComboAction(cards=five_cards, target_card_type=discard_type)
        
        # Late-game pressure: attack weak next player or shrink deck.
        if attack_cards and self._should_attack_for_pressure(view, draw_risk, safe_draws):
            return PlayCardAction(card=attack_cards[0])
        
        # If attacked and still unsafe, burn a Skip to reduce turns.
        if turns_remaining > 1 and skip_cards and safe_draws == 0:
            return PlayCardAction(card=skip_cards[0])
        
        return DrawCardAction()
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        nope_cards: tuple[Card, ...] = view.get_cards_of_type("NopeCard")
        if not nope_cards:
            return None
        
        nope_count: int = len(nope_cards)
        defuse_count: int = view.count_cards_of_type("DefuseCard")
        top_is_kitten: bool = self._top_is_kitten()
        
        event_type: EventType = triggering_event.event_type
        data: dict[str, Any] = triggering_event.data if triggering_event.data else dict[str, Any]()
        triggering_player_id: str | None = triggering_event.player_id
        
        if event_type == EventType.CARD_PLAYED:
            card_type: str | None = self._data_str(data, "card_type")
            target_id: str | None = self._data_str(data, "target")
            
            if card_type == "FavorCard" and target_id == view.my_id:
                lowest_value: int = self._lowest_card_value_in_hand(view)
                if self._should_nope_favor(lowest_value, nope_count, defuse_count):
                    return PlayCardAction(card=nope_cards[0])
            
            if card_type == "AttackCard":
                if triggering_player_id is not None and self._is_next_player(view, triggering_player_id):
                    if self._should_nope_attack(view, defuse_count):
                        return PlayCardAction(card=nope_cards[0])
                if top_is_kitten and triggering_player_id is not None:
                    if self._should_nope_to_force_draw(view, triggering_player_id, nope_count):
                        return PlayCardAction(card=nope_cards[0])
            
            if card_type in ("SkipCard", "ShuffleCard"):
                if top_is_kitten and triggering_player_id is not None:
                    if self._should_nope_to_force_draw(view, triggering_player_id, nope_count):
                        return PlayCardAction(card=nope_cards[0])
        
        if event_type == EventType.COMBO_PLAYED:
            combo_target: str | None = self._data_str(data, "target")
            if combo_target == view.my_id:
                expected_loss: float = self._expected_random_loss_value(view)
                if expected_loss >= 55.0:
                    return PlayCardAction(card=nope_cards[0])
                if defuse_count == 0 and expected_loss >= 35.0:
                    return PlayCardAction(card=nope_cards[0])
        
        return None
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        turns_remaining: int = view.my_turns_remaining
        remaining_defuse: int = view.count_cards_of_type("DefuseCard")
        
        avoid_count: int = view.count_cards_of_type("AttackCard") + view.count_cards_of_type("SkipCard")
        aggressive: bool = remaining_defuse > 0 or avoid_count >= 2
        
        if turns_remaining > 1:
            return draw_pile_size
        
        if len(view.other_players) == 1 and aggressive:
            return 0
        
        target_id: str | None = self._select_defuse_target(view)
        if target_id is None:
            return draw_pile_size
        
        distance: int | None = self._distance_to_player(view, view.my_id, target_id)
        if distance is None:
            return draw_pile_size
        
        if not aggressive:
            return draw_pile_size
        
        position: int = max(0, distance - 1)
        if position > draw_pile_size:
            position = draw_pile_size
        return position
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        hand: tuple[Card, ...] = view.my_hand
        best_card: Card = hand[0]
        best_value: int = self._card_value(best_card)
        
        card: Card
        for card in hand:
            value: int = self._card_value(card)
            if value < best_value:
                best_card = card
                best_value = value
        
        return best_card
    
    def on_explode(self, view: BotView) -> None:
        return

    # --- Helpers: tracking ---
    
    def _sync_players_from_view(self, view: BotView) -> None:
        player_ids: tuple[str, ...] = view.turn_order
        pid: str
        for pid in player_ids:
            self._ensure_player(pid)
    
    def _ensure_player(self, player_id: str) -> None:
        if player_id not in self._known_hands:
            self._known_hands[player_id] = dict[str, int]()
    
    def _adjust_known_card(self, player_id: str, card_type: str, delta: int) -> None:
        self._ensure_player(player_id)
        counts: dict[str, int] = self._known_hands[player_id]
        current: int = counts.get(card_type, 0)
        new_count: int = current + delta
        if new_count <= 0:
            if card_type in counts:
                del counts[card_type]
            return
        counts[card_type] = new_count
    
    def _apply_peek(self, card_types: Iterable[str]) -> None:
        index: int
        card_type: str
        for index, card_type in enumerate(card_types):
            if index >= len(self._known_top):
                self._known_top.append(None)
            self._known_top[index] = card_type
    
    def _apply_draw_from_top(self, card_type: str | None) -> None:
        if not self._known_top:
            return
        known_top: str | None = self._known_top[0]
        if known_top is None or card_type is None or known_top == card_type:
            self._known_top.pop(0)
            return
        self._known_top = []
    
    def _apply_insert_at(self, position: int, card_type: str) -> None:
        if position < 0:
            return
        while len(self._known_top) <= position:
            self._known_top.append(None)
        self._known_top[position] = card_type
    
    def _trim_known_top(self, draw_pile_count: int) -> None:
        if draw_pile_count < 0:
            return
        while len(self._known_top) > draw_pile_count:
            self._known_top.pop()

    # --- Helpers: evaluation ---
    
    def _safe_draws_from_top(self) -> int:
        safe: int = 0
        card_type: str | None
        for card_type in self._known_top:
            if card_type is None:
                break
            if card_type == "ExplodingKittenCard":
                break
            safe += 1
        return safe
    
    def _top_is_kitten(self) -> bool:
        return bool(self._known_top) and self._known_top[0] == "ExplodingKittenCard"
    
    def _estimate_draw_risk(self, view: BotView) -> float:
        draw_pile_count: int = view.draw_pile_count
        if draw_pile_count <= 0:
            return 0.0
        alive_players: int = len(view.other_players) + 1
        kittens_remaining: int = max(0, alive_players - 1)
        return kittens_remaining / draw_pile_count
    
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
        target_id: str | None = self._select_defuse_target(view)
        if target_id is None:
            return False
        avoid_target: int = self._get_avoid_count(target_id)
        if avoid_target == 0:
            return True
        return False
    
    def _choose_avoid_action_for_kitten(
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
        best_target: str | None = None
        best_value: float = -1.0
        target_id: str
        card_count: int
        for target_id, card_count in view.other_player_card_counts.items():
            if card_count <= 0:
                continue
            value: float = self._expected_favor_value(view, target_id)
            if value > best_value:
                best_value = value
                best_target = target_id
        if best_target is None:
            return None
        return (best_target, best_value)
    
    def _select_best_steal_target(self, view: BotView) -> str | None:
        best_target: str | None = None
        best_value: float = -1.0
        target_id: str
        card_count: int
        for target_id, card_count in view.other_player_card_counts.items():
            if card_count <= 0:
                continue
            value: float = self._expected_steal_value(view, target_id)
            if value > best_value:
                best_value = value
                best_target = target_id
        return best_target
    
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
        expected_gain: float = self._expected_steal_value(view, target_id)
        combo_cost: int = self._combo_cost(combo_cards)
        if expected_gain <= 0.0:
            return False
        if draw_risk >= 0.35 and defuse_count == 0:
            return False
        return expected_gain >= float(combo_cost + 5)
    
    def _should_attack_for_pressure(self, view: BotView, draw_risk: float, safe_draws: int) -> bool:
        if safe_draws > 0 and draw_risk <= 0.15:
            return False
        next_player: str | None = self._get_next_player(view, view.my_id)
        if next_player is None:
            return False
        vulnerability: int = self._vulnerability_score(view, next_player)
        if vulnerability >= 4:
            return True
        if view.draw_pile_count <= max(2, len(view.other_players) + 1):
            return True
        return draw_risk >= 0.35 and view.count_cards_of_type("DefuseCard") == 0
    
    def _select_three_of_a_kind_combo(self, view: BotView) -> tuple[Card, ...] | None:
        hand: tuple[Card, ...] = view.my_hand
        by_type: dict[str, list[Card]] = dict[str, list[Card]]()
        
        card: Card
        for card in hand:
            if "CatCard" not in card.card_type:
                continue
            if card.card_type not in by_type:
                by_type[card.card_type] = list[Card]()
            by_type[card.card_type].append(card)
        
        best_type: str | None = None
        best_count: int = 0
        card_type: str
        cards_of_type: list[Card]
        for card_type, cards_of_type in by_type.items():
            if len(cards_of_type) >= 3 and len(cards_of_type) > best_count:
                best_type = card_type
                best_count = len(cards_of_type)
        
        if best_type is None:
            return None
        
        selected_cards: list[Card] = []
        for card in by_type[best_type][:3]:
            selected_cards.append(card)
        return tuple(selected_cards)
    
    def _select_named_steal_target(self, view: BotView) -> tuple[str, str, int] | None:
        best_target: str | None = None
        best_card_type: str | None = None
        best_value: int = -1
        
        target_id: str
        for target_id in view.other_players:
            best_known: tuple[str, int] | None = self._best_known_card_to_steal(target_id)
            if best_known is None:
                continue
            card_type: str = best_known[0]
            value: int = best_known[1]
            if value > best_value:
                best_value = value
                best_target = target_id
                best_card_type = card_type
        
        if best_target is None or best_card_type is None:
            return None
        
        return (best_target, best_card_type, best_value)
    
    def _best_known_card_to_steal(self, target_id: str) -> tuple[str, int] | None:
        counts: dict[str, int] = self._known_hands.get(target_id, dict[str, int]())
        best_type: str | None = None
        best_value: int = -1
        card_type: str
        count: int
        for card_type, count in counts.items():
            if count <= 0:
                continue
            value: int = self._card_value_by_type(card_type)
            if value > best_value:
                best_value = value
                best_type = card_type
        
        if best_type is None:
            return None
        
        return (best_type, best_value)
    
    def _should_play_three_of_kind(
        self,
        combo_cards: tuple[Card, ...],
        target_value: int,
    ) -> bool:
        combo_cost: int = self._combo_cost(combo_cards)
        return target_value >= combo_cost + 10
    
    def _select_best_discard_pick(self, view: BotView) -> tuple[str, int] | None:
        discard_pile: tuple[Card, ...] = view.discard_pile
        if not discard_pile:
            return None
        
        best_type: str | None = None
        best_value: int = -1
        card: Card
        for card in discard_pile:
            value: int = self._card_value_by_type(card.card_type)
            if value > best_value:
                best_value = value
                best_type = card.card_type
        
        if best_type is None:
            return None
        
        return (best_type, best_value)

    def _select_two_of_a_kind_combo(self, view: BotView) -> tuple[Card, ...] | None:
        hand: tuple[Card, ...] = view.my_hand
        by_type: dict[str, list[Card]] = dict[str, list[Card]]()
        
        card: Card
        for card in hand:
            if "CatCard" not in card.card_type:
                continue
            if card.card_type not in by_type:
                by_type[card.card_type] = list[Card]()
            by_type[card.card_type].append(card)
        
        best_type: str | None = None
        best_count: int = 0
        card_type: str
        cards_of_type: list[Card]
        for card_type, cards_of_type in by_type.items():
            if len(cards_of_type) >= 2 and len(cards_of_type) > best_count:
                best_type = card_type
                best_count = len(cards_of_type)
        
        if best_type is None:
            return None
        
        selected_cards: list[Card] = []
        for card in by_type[best_type][:2]:
            selected_cards.append(card)
        return tuple(selected_cards)
    
    def _select_five_different_combo(self, view: BotView) -> tuple[Card, ...] | None:
        combo_candidates: list[Card] = []
        card: Card
        for card in view.my_hand:
            if card.can_combo():
                combo_candidates.append(card)
        
        if len(combo_candidates) < 5:
            return None
        
        combo_candidates.sort(key=self._card_value)
        
        selected: list[Card] = []
        seen_types: set[str] = set()
        for card in combo_candidates:
            if card.card_type in seen_types:
                continue
            selected.append(card)
            seen_types.add(card.card_type)
            if len(selected) == 5:
                break
        
        if len(selected) < 5:
            return None
        
        return tuple(selected)
    
    def _top_discard_value(self, view: BotView) -> int:
        discard_pile: tuple[Card, ...] = view.discard_pile
        if not discard_pile:
            return 0
        top_card: Card = discard_pile[-1]
        return self._card_value(top_card)
    
    def _combo_cost(self, cards: tuple[Card, ...]) -> int:
        total: int = 0
        card: Card
        for card in cards:
            total += self._card_value(card)
        return total

    def _expected_favor_value(self, view: BotView, target_id: str) -> float:
        total_cards: int = view.other_player_card_counts.get(target_id, 0)
        if total_cards <= 0:
            return 0.0
        
        counts: dict[str, int] = self._known_hands.get(target_id, dict[str, int]())
        known_total: int = self._get_known_total(target_id)
        
        min_value: int = 1000
        card_type: str
        count: int
        for card_type, count in counts.items():
            if count <= 0:
                continue
            value: int = self._card_value_by_type(card_type)
            if value < min_value:
                min_value = value
        
        unknown_count: int = max(0, total_cards - known_total)
        if unknown_count > 0:
            min_value = min(min_value, 10)
        if min_value == 1000:
            min_value = 10
        
        return float(min_value)
    
    def _expected_steal_value(self, view: BotView, target_id: str) -> float:
        total_cards: int = view.other_player_card_counts.get(target_id, 0)
        if total_cards <= 0:
            return 0.0
        
        counts: dict[str, int] = self._known_hands.get(target_id, dict[str, int]())
        known_total: int = 0
        value_sum: int = 0
        
        card_type: str
        count: int
        for card_type, count in counts.items():
            if count <= 0:
                continue
            known_total += count
            value_sum += self._card_value_by_type(card_type) * count
        
        unknown_count: int = max(0, total_cards - known_total)
        unknown_value: int = 25
        total_value: int = value_sum + (unknown_value * unknown_count)
        
        return total_value / total_cards
    
    def _expected_random_loss_value(self, view: BotView) -> float:
        hand: tuple[Card, ...] = view.my_hand
        if not hand:
            return 0.0
        total_value: int = 0
        card: Card
        for card in hand:
            total_value += self._card_value(card)
        return total_value / len(hand)
    
    def _lowest_card_value_in_hand(self, view: BotView) -> int:
        hand: tuple[Card, ...] = view.my_hand
        lowest: int = 1000
        card: Card
        for card in hand:
            value: int = self._card_value(card)
            if value < lowest:
                lowest = value
        if lowest == 1000:
            return 0
        return lowest
    
    def _should_nope_favor(self, lowest_value: int, nope_count: int, defuse_count: int) -> bool:
        if lowest_value >= 60:
            return True
        if defuse_count == 0 and lowest_value >= 40:
            return True
        return nope_count >= 2 and lowest_value >= 30
    
    def _should_nope_attack(self, view: BotView, defuse_count: int) -> bool:
        avoid_count: int = view.count_cards_of_type("AttackCard") + view.count_cards_of_type("SkipCard")
        if avoid_count > 0:
            return False
        draw_risk: float = self._estimate_draw_risk(view)
        safe_draws: int = self._safe_draws_from_top()
        if safe_draws > 0:
            draw_risk = 0.0
        if defuse_count == 0:
            return draw_risk >= 0.20
        return draw_risk >= 0.35
    
    def _should_nope_to_force_draw(self, view: BotView, triggering_player_id: str, nope_count: int) -> bool:
        if triggering_player_id == view.my_id:
            return False
        if view.current_player != triggering_player_id:
            return False
        remaining_avoids: int = self._get_avoid_count(triggering_player_id)
        shuffle_count: int = self._get_known_count(triggering_player_id, "ShuffleCard")
        if remaining_avoids + shuffle_count > 1 and nope_count < 2:
            return False
        if nope_count >= 2:
            return True
        return view.count_cards_of_type("DefuseCard") > 0
    
    def _select_defuse_target(self, view: BotView) -> str | None:
        best_target: str | None = None
        best_score: int = -1
        target_id: str
        for target_id in view.other_players:
            score: int = self._vulnerability_score(view, target_id)
            if score > best_score:
                best_score = score
                best_target = target_id
        return best_target
    
    def _vulnerability_score(self, view: BotView, player_id: str) -> int:
        defuse_count: int = self._get_known_count(player_id, "DefuseCard")
        avoid_count: int = self._get_avoid_count(player_id)
        hand_count: int = view.other_player_card_counts.get(player_id, 0)
        
        score: int = 0
        if defuse_count <= 0:
            score += 3
        if avoid_count <= 0:
            score += 2
        if hand_count <= 2:
            score += 1
        return score

    def _get_known_count(self, player_id: str, card_type: str) -> int:
        counts: dict[str, int] = self._known_hands.get(player_id, dict[str, int]())
        return counts.get(card_type, 0)
    
    def _get_known_total(self, player_id: str) -> int:
        counts: dict[str, int] = self._known_hands.get(player_id, dict[str, int]())
        total: int = 0
        card_type: str
        count: int
        for card_type, count in counts.items():
            total += count
        return total
    
    def _get_avoid_count(self, player_id: str) -> int:
        attack_count: int = self._get_known_count(player_id, "AttackCard")
        skip_count: int = self._get_known_count(player_id, "SkipCard")
        return attack_count + skip_count
    
    def _is_next_player(self, view: BotView, player_id: str) -> bool:
        next_player: str | None = self._get_next_player(view, player_id)
        return next_player == view.my_id
    
    def _get_next_player(self, view: BotView, player_id: str) -> str | None:
        order: tuple[str, ...] = view.turn_order
        if not order:
            return None
        if player_id not in order:
            return None
        current_index: int = order.index(player_id)
        next_index: int = (current_index + 1) % len(order)
        return order[next_index]
    
    def _distance_to_player(self, view: BotView, from_id: str, to_id: str) -> int | None:
        order: tuple[str, ...] = view.turn_order
        if from_id not in order or to_id not in order:
            return None
        from_index: int = order.index(from_id)
        to_index: int = order.index(to_id)
        if to_index >= from_index:
            return to_index - from_index
        return len(order) - from_index + to_index
    
    def _card_value(self, card: Card) -> int:
        return self._card_value_by_type(card.card_type)
    
    def _card_value_by_type(self, card_type: str) -> int:
        if card_type == "DefuseCard":
            return 100
        if card_type == "NopeCard":
            return 90
        if card_type == "AttackCard":
            return 70
        if card_type == "SkipCard":
            return 60
        if card_type == "ShuffleCard":
            return 55
        if card_type == "SeeTheFutureCard":
            return 45
        if card_type == "FavorCard":
            return 35
        if "CatCard" in card_type:
            return 10
        return 15
    
    # --- Helpers: event data parsing ---
    
    def _data_str(self, data: dict[str, Any], key: str) -> str | None:
        value: Any = data.get(key)
        if isinstance(value, str):
            return value
        return None
    
    def _data_int(self, data: dict[str, Any], key: str) -> int | None:
        value: Any = data.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        return None
    
    def _data_str_list(self, data: dict[str, Any], key: str) -> list[str]:
        value: Any = data.get(key)
        items: list[str] = []
        if isinstance(value, list):
            item: Any
            for item in value:
                if isinstance(item, str):
                    items.append(item)
        return items
