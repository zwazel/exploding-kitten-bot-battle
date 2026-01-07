"""
Tests for the card system.

These tests verify card behavior, registry functionality,
and deck creation from configuration.
"""

import pytest
from pathlib import Path
import tempfile
import json

from game.cards.base import Card
from game.cards.registry import CardRegistry
from game.cards.placeholder import (
    DrawCard,
    register_placeholder_cards,
)
from game.cards.action_cards import SkipCard, NopeCard, AttackCard
from game.cards import register_all_cards
from game.cards.cat_cards import TacoCatCard
from game.bots.view import BotView
from game.history import GameEvent, EventType


# Create a minimal BotView for testing
def create_test_view(is_my_turn: bool = True) -> BotView:
    """Create a minimal BotView for testing card.can_play()."""
    return BotView(
        my_id="test_player",
        my_hand=(),
        my_turns_remaining=1,
        discard_pile=(),
        draw_pile_count=10,
        other_players=("other_player",),
        other_player_card_counts={"other_player": 5},
        current_player="test_player" if is_my_turn else "other_player",
        turn_order=("test_player", "other_player"),
        is_my_turn=is_my_turn,
        recent_events=(),
    )


class TestCardBase:
    """Tests for basic card behavior."""
    
    def test_skip_card_can_play_on_own_turn(self) -> None:
        """SkipCard should be playable on own turn."""
        card: Card = SkipCard()
        view: BotView = create_test_view(is_my_turn=True)
        
        assert card.can_play(view, is_own_turn=True) is True
    
    def test_skip_card_cannot_play_off_turn(self) -> None:
        """SkipCard should not be playable on other's turn."""
        card: Card = SkipCard()
        view: BotView = create_test_view(is_my_turn=False)
        
        assert card.can_play(view, is_own_turn=False) is False
    
    def test_nope_card_is_reaction(self) -> None:
        """NopeCard should be playable as a reaction."""
        card: Card = NopeCard()
        
        assert card.can_play_as_reaction() is True
    
    def test_skip_card_is_not_reaction(self) -> None:
        """SkipCard should not be playable as a reaction."""
        card: Card = SkipCard()
        
        assert card.can_play_as_reaction() is False
    
    def test_cat_card_can_combo(self) -> None:
        """TacoCatCard should be usable in combos."""
        card: Card = TacoCatCard()
        
        assert card.can_combo() is True
    
    def test_action_cards_can_combo(self) -> None:
        """Action cards (Skip, Attack, etc.) CAN be used in combos."""
        card: Card = SkipCard()
        
        # Per game design, action cards can be used in combos
        assert card.can_combo() is True
    
    def test_cat_card_playable_alone(self) -> None:
        """Cat cards can be played alone (no effect)."""
        card: Card = TacoCatCard()
        view: BotView = create_test_view(is_my_turn=True)
        
        # Cat cards can be played on own turn
        assert card.can_play(view, is_own_turn=True) is True
    
    def test_card_repr(self) -> None:
        """Cards should have a readable repr."""
        card: Card = SkipCard()
        
        assert "SkipCard" in repr(card)
        assert "Skip" in repr(card)


class TestCardRegistry:
    """Tests for the CardRegistry class."""
    
    def test_register_card_class(self) -> None:
        """Cards should be registerable."""
        registry: CardRegistry = CardRegistry()
        registry.register_with_type("SkipCard", SkipCard)
        
        assert "SkipCard" in registry.get_registered_types()
    
    def test_register_duplicate_raises(self) -> None:
        """Registering a duplicate type should raise."""
        registry: CardRegistry = CardRegistry()
        registry.register_with_type("SkipCard", SkipCard)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register_with_type("SkipCard", SkipCard)
    
    def test_create_card(self) -> None:
        """Registry should create card instances."""
        registry: CardRegistry = CardRegistry()
        registry.register_with_type("SkipCard", SkipCard)
        
        card: Card = registry.create_card("SkipCard")
        
        assert isinstance(card, SkipCard)
    
    def test_create_unknown_card_raises(self) -> None:
        """Creating an unknown card type should raise."""
        registry: CardRegistry = CardRegistry()
        
        with pytest.raises(ValueError, match="Unknown card type"):
            registry.create_card("UnknownCard")
    
    def test_create_deck_from_dict(self) -> None:
        """Registry should create a deck from configuration."""
        registry: CardRegistry = CardRegistry()
        register_all_cards(registry)
        
        config: dict[str, int] = {
            "SkipCard": 2,
            "NopeCard": 3,
            "TacoCatCard": 4,
        }
        
        deck: list[Card] = registry.create_deck(config)
        
        assert len(deck) == 9
        skip_count: int = sum(1 for c in deck if isinstance(c, SkipCard))
        nope_count: int = sum(1 for c in deck if isinstance(c, NopeCard))
        cat_count: int = sum(1 for c in deck if isinstance(c, TacoCatCard))
        
        assert skip_count == 2
        assert nope_count == 3
        assert cat_count == 4
    
    def test_create_deck_from_file(self) -> None:
        """Registry should create a deck from a JSON file."""
        registry: CardRegistry = CardRegistry()
        register_all_cards(registry)
        
        config: dict = {
            "cards": {
                "SkipCard": 1,
                "AttackCard": 2,
            }
        }
        
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
        ) as f:
            json.dump(config, f)
            config_path: str = f.name
        
        try:
            deck: list[Card] = registry.create_deck_from_file(config_path)
            
            assert len(deck) == 3
            skip_count: int = sum(1 for c in deck if isinstance(c, SkipCard))
            attack_count: int = sum(1 for c in deck if isinstance(c, AttackCard))
            
            assert skip_count == 1
            assert attack_count == 2
        finally:
            Path(config_path).unlink()


class TestPlaceholderCards:
    """Tests for the placeholder card implementations."""
    
    def test_register_placeholder_cards(self) -> None:
        """register_placeholder_cards should register placeholder cards."""
        registry: CardRegistry = CardRegistry()
        register_placeholder_cards(registry)
        
        registered: tuple[str, ...] = registry.get_registered_types()
        
        assert "DrawCard" in registered
        assert "SkipCard" in registered
        assert "NopeCard" in registered
        assert "AttackCard" in registered
        # ComboCard is the old placeholder - no longer used
        # TacoCatCard is now from cat_cards, not placeholder
    
    def test_draw_card_properties(self) -> None:
        """DrawCard should have correct properties."""
        card: DrawCard = DrawCard()
        
        assert card.name == "Draw"
        assert card.card_type == "DrawCard"
        assert card.can_play_as_reaction() is False
        assert card.can_combo() is False
    
    def test_attack_card_properties(self) -> None:
        """AttackCard should have correct properties."""
        card: AttackCard = AttackCard()
        
        assert card.name == "Attack"
        assert card.card_type == "AttackCard"
        assert card.can_play_as_reaction() is False
