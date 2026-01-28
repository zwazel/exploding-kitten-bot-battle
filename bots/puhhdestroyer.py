import random
from collections import Counter, defaultdict

from game.bots.base import (
    Bot,
    Action,
    DrawCardAction,
    PlayCardAction,
    PlayComboAction,
)
from game.bots.view import BotView
from game.cards.base import Card
from game.history import GameEvent, EventType


class p_destroyer(Bot):
    """
    Maximum-strength, non-cheating Exploding Kittens bot.
    """

    def __init__(self) -> None:
        # Memory
        self.known_future: list[str] = []
        self.no_defuse: set[str] = set()
        self.last_draw: dict[str, int] = defaultdict(int)
        self.turn_counter = 0

        self.trash = [
            "Calculated.",
            "Skill issue.",
            "Unlucky.",
            "You should have skipped.",
            "Predictable.",
            "That was forced.",
        ]

    @property
    def name(self) -> str:
        return "ApocalypseBot"

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _has(self, hand, t):
        return any(c.card_type == t for c in hand)

    def _get(self, hand, t):
        return next(c for c in hand if c.card_type == t)

    def _count(self, hand, t):
        return sum(c.card_type == t for c in hand)

    def _danger(self, view: BotView) -> float:
        players = len(view.other_players) + 1
        return players / max(1, view.draw_pile_count)

    def _richest_enemy(self, view: BotView) -> str:
        return max(
            view.other_players,
            key=lambda p: view.other_player_card_counts.get(p, 0),
        )

    # ------------------------------------------------------------------
    # Turn Logic
    # ------------------------------------------------------------------

    def take_turn(self, view: BotView) -> Action:
        self.turn_counter += 1
        hand = view.my_hand
        danger = self._danger(view)

        # --------------------------------------------------------------
        # 1. Use known future
        # --------------------------------------------------------------
        if self.known_future:
            top = self.known_future[0]

            if top == "ExplodingKittenCard":
                if self._has(hand, "AttackCard"):
                    return PlayCardAction(self._get(hand, "AttackCard"))
                if self._has(hand, "SkipCard"):
                    return PlayCardAction(self._get(hand, "SkipCard"))
                if self._has(hand, "ShuffleCard"):
                    return PlayCardAction(self._get(hand, "ShuffleCard"))

        # --------------------------------------------------------------
        # 2. Attack chains
        # --------------------------------------------------------------
        if danger > 0.3 and self._has(hand, "AttackCard"):
            return PlayCardAction(self._get(hand, "AttackCard"))

        # --------------------------------------------------------------
        # 3. Skip to survive
        # --------------------------------------------------------------
        if danger > 0.2 and self._has(hand, "SkipCard"):
            return PlayCardAction(self._get(hand, "SkipCard"))

        # --------------------------------------------------------------
        # 4. Peek aggressively
        # --------------------------------------------------------------
        if self._has(hand, "SeeTheFutureCard"):
            return PlayCardAction(self._get(hand, "SeeTheFutureCard"))

        # --------------------------------------------------------------
        # 5. Combos (intelligent)
        # --------------------------------------------------------------
        combo_cards = [c for c in hand if c.can_combo()]
        by_type = Counter(c.card_type for c in combo_cards)

        # Three-of-a-kind → steal Defuse
        for t, n in by_type.items():
            if n >= 3 and view.other_players:
                return PlayComboAction(
                    cards=tuple(c for c in combo_cards if c.card_type == t)[:3],
                    target_player_id=self._richest_enemy(view),
                    target_card_type="DefuseCard",
                )

        # Two-of-a-kind → bomb-likely target
        for t, n in by_type.items():
            if n >= 2 and view.other_players:
                target = max(
                    view.other_players,
                    key=lambda p: self.last_draw[p],
                )
                return PlayComboAction(
                    cards=tuple(c for c in combo_cards if c.card_type == t)[:2],
                    target_player_id=target,
                )

        # --------------------------------------------------------------
        # 6. Favor snipe
        # --------------------------------------------------------------
        if self._has(hand, "FavorCard") and view.other_players:
            return PlayCardAction(
                self._get(hand, "FavorCard"),
                self._richest_enemy(view),
            )

        # --------------------------------------------------------------
        # 7. Draw only if forced
        # --------------------------------------------------------------
        return DrawCardAction()

    # ------------------------------------------------------------------
    # Reactions (Nope God)
    # ------------------------------------------------------------------

    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        if not self._has(view.my_hand, "NopeCard"):
            return None

        if triggering_event.event_type == EventType.CARD_PLAYED:
            card = triggering_event.data.get("card_type")

            if card in {
                "AttackCard",
                "FavorCard",
                "ShuffleCard",
                "SeeTheFutureCard",
                "ThreeOfAKindCombo",
                "FiveDifferentCombo",
            }:
                if random.random() < 0.9:
                    view.say(random.choice(self.trash))
                    return PlayCardAction(self._get(view.my_hand, "NopeCard"))

        return None

    # ------------------------------------------------------------------
    # Defuse Placement
    # ------------------------------------------------------------------

    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        # Kill next player
        return 0

    # ------------------------------------------------------------------
    # Favor Logic
    # ------------------------------------------------------------------

    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        hand = list(view.my_hand)

        cats = [c for c in hand if "Cat" in c.card_type]
        if cats:
            return random.choice(cats)

        for junk in ("ShuffleCard", "SeeTheFutureCard", "FavorCard"):
            for c in hand:
                if c.card_type == junk:
                    return c

        non_critical = [
            c for c in hand if c.card_type not in ("DefuseCard", "NopeCard")
        ]
        return random.choice(non_critical or hand)

    # ------------------------------------------------------------------
    # Event Tracking
    # ------------------------------------------------------------------

    def on_event(self, event: GameEvent, view: BotView) -> None:
        if event.event_type == EventType.CARD_DRAWN:
            self.last_draw[event.player_id] += 1

        if event.event_type == EventType.CARD_PLAYED:
            if event.data.get("card_type") == "SeeTheFutureCard":
                if event.player_id == view.my_id:
                    self.known_future = event.data.get("future", [])

        if event.event_type == EventType.EXPLODING_KITTEN_DRAWN:
            self.no_defuse.add(event.player_id)

    def on_explode(self, view: BotView) -> None:
        view.say("Impossible outcome.")
