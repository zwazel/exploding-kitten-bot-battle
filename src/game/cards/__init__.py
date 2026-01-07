"""
Card system package.

Contains:
- base: Abstract base class for all cards
- registry: Card type registration and deck creation
- exploding_kitten: Core cards (Exploding Kitten, Defuse)
- action_cards: Action cards (Nope, Attack, Skip, etc.)
- cat_cards: Cat cards for combos
"""

from game.cards.base import Card
from game.cards.registry import CardRegistry

# Core cards
from game.cards.exploding_kitten import (
    ExplodingKittenCard,
    DefuseCard,
)

# Action cards
from game.cards.action_cards import (
    NopeCard,
    AttackCard,
    SkipCard,
    FavorCard,
    ShuffleCard,
    SeeTheFutureCard,
)

# Cat cards
from game.cards.cat_cards import (
    CatCard,
    TacoCatCard,
    HairyPotatoCatCard,
    BeardCatCard,
    RainbowRalphingCatCard,
    CattermelonCard,
)

__all__: list[str] = [
    # Base
    "Card",
    "CardRegistry",
    # Core
    "ExplodingKittenCard",
    "DefuseCard",
    # Action
    "NopeCard",
    "AttackCard",
    "SkipCard",
    "FavorCard",
    "ShuffleCard",
    "SeeTheFutureCard",
    # Cat
    "CatCard",
    "TacoCatCard",
    "HairyPotatoCatCard",
    "BeardCatCard",
    "RainbowRalphingCatCard",
    "CattermelonCard",
]


def register_all_cards(registry: CardRegistry) -> None:
    """
    Register all game cards with a registry.
    
    Args:
        registry: The card registry to register with.
    """
    # Core cards
    registry.register_with_type("ExplodingKittenCard", ExplodingKittenCard)
    registry.register_with_type("DefuseCard", DefuseCard)
    
    # Action cards
    registry.register_with_type("NopeCard", NopeCard)
    registry.register_with_type("AttackCard", AttackCard)
    registry.register_with_type("SkipCard", SkipCard)
    registry.register_with_type("FavorCard", FavorCard)
    registry.register_with_type("ShuffleCard", ShuffleCard)
    registry.register_with_type("SeeTheFutureCard", SeeTheFutureCard)
    
    # Cat cards
    registry.register_with_type("TacoCatCard", TacoCatCard)
    registry.register_with_type("HairyPotatoCatCard", HairyPotatoCatCard)
    registry.register_with_type("BeardCatCard", BeardCatCard)
    registry.register_with_type("RainbowRalphingCatCard", RainbowRalphingCatCard)
    registry.register_with_type("CattermelonCard", CattermelonCard)
