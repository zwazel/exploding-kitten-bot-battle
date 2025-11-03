"""Card definitions for Exploding Kittens game."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class CardType(Enum):
    """Types of cards in Exploding Kittens."""
    EXPLODING_KITTEN = "Exploding Kitten"
    DEFUSE = "Defuse"
    SKIP = "Skip"
    SEE_THE_FUTURE = "See the Future"
    SHUFFLE = "Shuffle"
    FAVOR = "Favor"
    ATTACK = "Attack"
    NOPE = "Nope"
    # Cat cards for combos
    TACOCAT = "Tacocat"
    CATTERMELON = "Cattermelon"
    HAIRY_POTATO_CAT = "Hairy Potato Cat"
    BEARD_CAT = "Beard Cat"
    RAINBOW_RALPHING_CAT = "Rainbow-Ralphing Cat"


class ComboType(Enum):
    """Types of card combos in Exploding Kittens."""
    TWO_OF_A_KIND = "2-of-a-kind"
    THREE_OF_A_KIND = "3-of-a-kind"
    FIVE_UNIQUE = "5-unique"


class TargetContext(Enum):
    """
    Contexts for choosing a target player.
    
    Note: These enum values are intentionally separate from ComboType even though
    they share similar values. TargetContext represents WHY a target is being chosen
    (the context/reason), while ComboType represents WHAT type of combo is being played.
    This separation provides better type safety and clarity at the call sites.
    """
    FAVOR = "favor"
    TWO_OF_A_KIND = "2-of-a-kind"
    THREE_OF_A_KIND = "3-of-a-kind"


class ActionType(Enum):
    """Types of actions that can occur in the game."""
    CARD_PLAY = "card_play"
    COMBO_PLAY = "combo_play"
    CARD_DRAW = "card_draw"
    CARD_STEAL = "card_steal"
    CARD_REQUEST = "card_request"
    EXPLODING_KITTEN_DRAW = "exploding_kitten_draw"
    DEFUSE = "defuse"
    ELIMINATION = "elimination"
    NOPE = "nope"


@dataclass
class GameAction:
    """
    Represents a game action for notification purposes.
    Provides type-safe action descriptions instead of free-form strings.
    """
    action_type: ActionType
    player: str
    card: Optional[CardType] = None
    combo_type: Optional[ComboType] = None
    target: Optional[str] = None
    cards: Optional[List[CardType]] = None
    success: Optional[bool] = None


@dataclass
class Card:
    """Represents a card in the game."""
    card_type: CardType

    def __str__(self):
        return self.card_type.value

    def __repr__(self):
        return f"Card({self.card_type.value})"
