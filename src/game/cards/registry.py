"""
Card registry for registering card types and creating decks.

The registry maps card type identifiers to card classes, enabling
deck creation from configuration files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from game.cards.base import Card


class CardRegistry:
    """
    Registry for card types.
    
    Card classes are registered with the registry, which then enables
    creating decks from configuration files or dictionaries.
    """
    
    def __init__(self) -> None:
        """Initialize an empty card registry."""
        self._card_classes: dict[str, type[Card]] = {}
    
    def register(self, card_class: type[Card]) -> type[Card]:
        """
        Register a card class with the registry.
        
        Can be used as a decorator:
            @registry.register
            class MyCard(Card):
                ...
        
        Args:
            card_class: The card class to register.
            
        Returns:
            The card class (for decorator usage).
            
        Raises:
            ValueError: If a card with this type is already registered.
        """
        # Create a temporary instance to get the card_type
        # This is a bit of a hack, but avoids needing a class method
        temp_instance: Card = object.__new__(card_class)
        # Call __init__ if needed for type property to work
        if hasattr(card_class, "__init__"):
            try:
                card_class.__init__(temp_instance)  # type: ignore[misc]
            except TypeError:
                pass  # Some cards may need arguments
        
        card_type: str = card_class.__name__  # Use class name as type
        
        if card_type in self._card_classes:
            raise ValueError(
                f"Card type '{card_type}' is already registered"
            )
        
        self._card_classes[card_type] = card_class
        return card_class
    
    def register_with_type(self, card_type: str, card_class: type[Card]) -> None:
        """
        Register a card class with an explicit type identifier.
        
        Args:
            card_type: The type identifier for the card.
            card_class: The card class to register.
            
        Raises:
            ValueError: If a card with this type is already registered.
        """
        if card_type in self._card_classes:
            raise ValueError(
                f"Card type '{card_type}' is already registered"
            )
        self._card_classes[card_type] = card_class
    
    def get_card_class(self, card_type: str) -> type[Card] | None:
        """
        Get the card class for a given type.
        
        Args:
            card_type: The type identifier.
            
        Returns:
            The card class, or None if not found.
        """
        return self._card_classes.get(card_type)
    
    def get_registered_types(self) -> tuple[str, ...]:
        """
        Get all registered card types.
        
        Returns:
            Tuple of registered type identifiers.
        """
        return tuple(self._card_classes.keys())
    
    def create_card(self, card_type: str) -> Card:
        """
        Create a single card instance of the given type.
        
        Args:
            card_type: The type of card to create.
            
        Returns:
            A new card instance.
            
        Raises:
            ValueError: If the card type is not registered.
        """
        card_class: type[Card] | None = self._card_classes.get(card_type)
        if card_class is None:
            raise ValueError(f"Unknown card type: {card_type}")
        return card_class()
    
    def create_deck(self, config: dict[str, int]) -> list[Card]:
        """
        Create a deck of cards from a configuration.
        
        Args:
            config: Dictionary mapping card types to counts.
                    Example: {"SkipCard": 4, "NopeCard": 5}
            
        Returns:
            A list of card instances.
            
        Raises:
            ValueError: If any card type is not registered.
        """
        deck: list[Card] = []
        
        for card_type, count in config.items():
            card_class: type[Card] | None = self._card_classes.get(card_type)
            if card_class is None:
                raise ValueError(f"Unknown card type: {card_type}")
            
            for _ in range(count):
                deck.append(card_class())
        
        return deck
    
    def create_deck_from_file(self, config_path: str | Path) -> list[Card]:
        """
        Create a deck from a JSON configuration file.
        
        The file should have a "cards" key with type->count mapping:
        {
            "cards": {
                "SkipCard": 4,
                "NopeCard": 5
            }
        }
        
        Args:
            config_path: Path to the JSON configuration file.
            
        Returns:
            A list of card instances.
        """
        path: Path = Path(config_path)
        with path.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        
        cards_config: dict[str, int] = data.get("cards", {})
        return self.create_deck(cards_config)
