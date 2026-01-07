"""
Action cards for Exploding Kittens.

These cards have immediate effects when played:
- NopeCard: Cancel any action (playable as reaction, chainable)
- AttackCard: End turn, next player takes stacked turns
- SkipCard: End turn without drawing
- FavorCard: Force another player to give you a card
- ShuffleCard: Shuffle the draw pile
- SeeTheFutureCard: Peek at the top 3 cards
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from game.cards.base import Card

if TYPE_CHECKING:
    from game.bots.view import BotView
    from game.engine import GameEngine


class NopeCard(Card):
    """
    The Nope card.
    
    Can be played at any time to cancel any action except Exploding Kitten
    or Defuse. Nopes are chainable - a Nope can be Noped, and so on.
    Odd number of Nopes = action cancelled, even = action proceeds.
    
    Can also be played on own turn (does nothing, but valid play).
    """
    
    @property
    def name(self) -> str:
        return "Nope"
    
    @property
    def card_type(self) -> str:
        return "NopeCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        # Can be played on own turn (does nothing useful, but allowed)
        return is_own_turn
    
    def can_play_as_reaction(self) -> bool:
        # Primary use: as a reaction to cancel actions
        return True
    
    def can_combo(self) -> bool:
        # Nope cannot be used in combos
        return False
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # When played on own turn, does nothing
        # When played as reaction, the cancellation is handled by engine
        pass  # Nope effect is handled by reaction system


class AttackCard(Card):
    """
    The Attack card.
    
    End your turn without drawing. The next player must take 2 turns.
    If the attacked player plays an Attack card, the attack stacks:
    they transfer their remaining turns + 2 to the next player.
    """
    
    @property
    def name(self) -> str:
        return "Attack"
    
    @property
    def card_type(self) -> str:
        return "AttackCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        return is_own_turn
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def can_combo(self) -> bool:
        return True
    
    def ends_turn(self) -> bool:
        return True
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # Get extra turns beyond the normal 1 turn (for attack stacking)
        # If player has 2 turns remaining, they have 1 extra turn to transfer
        current_remaining: int = engine._turn_manager.get_turns_remaining(player_id)
        extra_from_stacking: int = max(0, current_remaining - 1)
        
        # End current player's turn without drawing
        engine._turn_manager.set_turns_remaining(player_id, 0)
        
        # Next player takes 2 turns + any stacked extra turns
        total_turns: int = 2 + extra_from_stacking
        engine.attack_next_player(player_id, total_turns)
        
        engine.log(f"  -> Next player takes {total_turns} turns!")


class SkipCard(Card):
    """
    The Skip card.
    
    End your turn without drawing a card. If you were attacked,
    this only ends ONE of your turns (you still have remaining turns).
    """
    
    @property
    def name(self) -> str:
        return "Skip"
    
    @property
    def card_type(self) -> str:
        return "SkipCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        return is_own_turn
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def can_combo(self) -> bool:
        return True
    
    def ends_turn(self) -> bool:
        return True
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # Skip just ends this turn without drawing
        # The turn manager will handle decrementing turns_remaining
        engine.skip_turn(player_id)


class FavorCard(Card):
    """
    The Favor card.
    
    Force any other player to give you a card of THEIR choice.
    The target player chooses which card to give.
    """
    
    @property
    def name(self) -> str:
        return "Favor"
    
    @property
    def card_type(self) -> str:
        return "FavorCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        # Can only play if there are other players with cards
        if not is_own_turn:
            return False
        return any(count > 0 for count in view.other_player_card_counts.values())
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def can_combo(self) -> bool:
        return True
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # The actual favor logic requires target selection
        # This is handled by the engine with the action's target_player_id
        pass  # Favor effect is handled by the engine's request_favor


class ShuffleCard(Card):
    """
    The Shuffle card.
    
    Shuffle the draw pile without viewing the cards.
    Useful to randomize after seeing the future or if you know
    where an Exploding Kitten is.
    """
    
    @property
    def name(self) -> str:
        return "Shuffle"
    
    @property
    def card_type(self) -> str:
        return "ShuffleCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        return is_own_turn
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def can_combo(self) -> bool:
        return True
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        engine.shuffle_deck()
        engine.log("  -> Draw pile shuffled!")


class SeeTheFutureCard(Card):
    """
    The See the Future card.
    
    Peek at the top 3 cards of the draw pile privately.
    Put them back in the same order (no rearranging).
    """
    
    @property
    def name(self) -> str:
        return "See the Future"
    
    @property
    def card_type(self) -> str:
        return "SeeTheFutureCard"
    
    def can_play(self, view: BotView, is_own_turn: bool) -> bool:
        return is_own_turn
    
    def can_play_as_reaction(self) -> bool:
        return False
    
    def can_combo(self) -> bool:
        return True
    
    def execute(self, engine: GameEngine, player_id: str) -> None:
        # Peek at top 3 cards (returned in draw order: first = next to draw)
        top_cards = engine.peek_draw_pile(player_id, count=3)
        if top_cards:
            # Display as "1st: X, 2nd: Y, 3rd: Z" for clarity
            card_strs: list[str] = []
            for i, card in enumerate(top_cards, 1):
                card_strs.append(f"{i}: {card.name}")
            engine.log(f"  -> Saw: {', '.join(card_strs)}")
