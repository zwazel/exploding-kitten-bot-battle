"""Game configuration for Exploding Kittens."""

from typing import Dict
from .cards import CardType


# Default deck configuration
DEFAULT_DECK_CONFIG: Dict[CardType, int] = {
    # Exploding Kittens are added based on number of players (num_players - 1)
    CardType.DEFUSE: 6,
    CardType.SKIP: 4,
    CardType.SEE_THE_FUTURE: 5,
    CardType.SHUFFLE: 4,
    CardType.FAVOR: 4,
    CardType.ATTACK: 4,
    CardType.NOPE: 5,
    # Cat cards - 4 of each type
    CardType.TACOCAT: 4,
    CardType.CATTERMELON: 4,
    CardType.HAIRY_POTATO_CAT: 4,
    CardType.BEARD_CAT: 4,
    CardType.RAINBOW_RALPHING_CAT: 4,
}


def get_deck_config(custom_config: Dict[CardType, int] = None) -> Dict[CardType, int]:
    """
    Get the deck configuration, optionally merging with custom config.
    
    Args:
        custom_config: Optional custom card counts to override defaults
        
    Returns:
        Dictionary mapping CardType to count
    """
    config = DEFAULT_DECK_CONFIG.copy()
    if custom_config:
        config.update(custom_config)
    return config
