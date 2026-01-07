"""
==============================================================================
RANDOM BOT - A Reference Implementation for Students
==============================================================================

This bot makes random decisions and serves as an educational example.
Use this as a starting point to understand how bots work, then create
your own bot with better strategy!

HOW TO CREATE YOUR OWN BOT:
1. Create a new .py file in the bots/ directory
2. Copy this file's structure
3. Implement smarter logic in each method
4. Run: python -m game.main --bot bots/your_bot.py:2

KEY CONCEPTS:
- BotView: Your "window" into the game (only shows what you're allowed to see)
- Action: What you want to do (play a card, draw, pass)
- GameEvent: Something that happened in the game
- Card: A card object with properties like card_type, name, etc.
"""

import random

# =============================================================================
# IMPORTS - These are the main classes you'll need
# =============================================================================

from game.bots.base import (
    Action,           # Base type for all actions
    Bot,              # The base class your bot must inherit from
    DrawCardAction,   # Action to draw a card (ends your turn)
    PlayCardAction,   # Action to play a single card
    PlayComboAction,  # Action to play multiple cards as a combo
)
from game.bots.view import BotView  # Your view of the game state
from game.cards.base import Card     # Card objects
from game.history import GameEvent   # Events that happen in the game


# =============================================================================
# THE BOT CLASS
# =============================================================================

class RandomBot(Bot):
    """
    A simple bot that makes random decisions.
    
    This bot is intentionally "dumb" - it just randomly picks what to do.
    Use this as a reference for HOW to implement the methods, then write
    your own bot with actual strategy!
    """
    
    # =========================================================================
    # REQUIRED: The name property
    # =========================================================================
    
    @property
    def name(self) -> str:
        """
        Return the bot's name. This is displayed during the game.
        
        TIP: Make it unique so you can identify your bot in the logs!
        """
        return "RandomBot"
    
    # =========================================================================
    # REQUIRED: take_turn - Called when it's your turn
    # =========================================================================
    
    def take_turn(self, view: BotView) -> Action:
        """
        Decide what to do on your turn.
        
        This is the main method where your strategy lives!
        
        Args:
            view: Your view of the game. Contains:
                  - view.my_hand: Your cards (tuple of Card objects)
                  - view.my_id: Your player ID
                  - view.other_players: IDs of other players
                  - view.draw_pile_count: How many cards in draw pile
                  - view.discard_pile: Cards in discard (visible to all)
                  - view.other_player_card_counts: How many cards each opponent has
        
        Returns:
            An Action object: DrawCardAction, PlayCardAction, or PlayComboAction
        
        IMPORTANT: You MUST eventually return DrawCardAction() to end your turn!
                   You can play cards before drawing, but must draw to end your turn.
        """
        
        # STRATEGY: This random bot has a 50% chance to play a card,
        # and 50% chance to just draw and end the turn.
        
        if random.random() < 0.5:
            # Try to find a playable card
            playable_cards = [
                card for card in view.my_hand
                if card.can_play(view, is_own_turn=True)
            ]
            
            if playable_cards:
                # Pick a random playable card
                card_to_play = random.choice(playable_cards)
                
                # If it's a Favor card, we need to specify a target
                if card_to_play.card_type == "FavorCard":
                    if view.other_players:
                        target = random.choice(view.other_players)
                        return PlayCardAction(card=card_to_play, target_player_id=target)
                
                return PlayCardAction(card=card_to_play)
        
        # Default: Draw a card to end the turn
        # This is the safe option and MUST be done eventually!
        return DrawCardAction()
    
    # =========================================================================
    # REQUIRED: on_event - Called when something happens in the game
    # =========================================================================
    
    def on_event(self, event: GameEvent, view: BotView) -> None:
        """
        React to events that happen in the game.
        
        This is called for EVERY event, so you can track what's happening.
        Useful for remembering what cards opponents have played.
        
        Args:
            event: The event that just happened. Contains:
                   - event.event_type: What kind of event (CARD_PLAYED, etc.)
                   - event.player_id: Who triggered the event
                   - event.data: Extra info (card_type, target, etc.)
            view: Current game state
        
        Returns:
            None (this is for information only, you can't take actions here)
        
        EXAMPLE EVENTS:
            - EventType.CARD_PLAYED: Someone played a card
            - EventType.CARD_DRAWN: Someone drew a card
            - EventType.PLAYER_ELIMINATED: Someone exploded!
        """
        
        # This random bot doesn't track anything, but a smart bot might:
        # - Remember which cards opponents have played
        # - Count how many Defuse cards are left
        # - Track where Exploding Kittens might be in the deck
        pass
    
    # =========================================================================
    # REQUIRED: react - Called when you can play a Nope card
    # =========================================================================
    
    def react(self, view: BotView, triggering_event: GameEvent) -> Action | None:
        """
        Decide whether to play a reaction card (like Nope).
        
        This is called when another player does something you can react to.
        You can play a Nope card to cancel their action!
        
        Args:
            view: Current game state
            triggering_event: The event you can react to (usually CARD_PLAYED)
        
        Returns:
            PlayCardAction with a Nope card to cancel the action, or
            None to let the action happen
        
        TIP: Be strategic with Nope cards! They're valuable.
             Consider: Is this action really hurting me?
        """
        
        # Find if we have a Nope card
        nope_cards = [c for c in view.my_hand if c.card_type == "NopeCard"]
        
        if nope_cards:
            # Random bot: 30% chance to use Nope
            if random.random() < 0.3:
                return PlayCardAction(card=nope_cards[0])
        
        # Don't react
        return None
    
    # =========================================================================
    # REQUIRED: choose_defuse_position - Called when you defuse a bomb
    # =========================================================================
    
    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        """
        Choose where to put the Exploding Kitten back in the deck.
        
        This is called after you successfully defuse an Exploding Kitten.
        You get to secretly put it back anywhere in the draw pile!
        
        Args:
            view: Current game state
            draw_pile_size: How many cards are in the draw pile
        
        Returns:
            An integer position:
            - 0 = top of the pile (next player gets it!)
            - draw_pile_size = bottom of the pile (safest for you)
            - Anywhere in between
        
        STRATEGY TIP: Put it where your opponent will draw it!
        """
        
        # Random position from top to bottom
        return random.randint(0, draw_pile_size)
    
    # =========================================================================
    # REQUIRED: choose_card_to_give - Called when hit by Favor
    # =========================================================================
    
    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        """
        Choose which card to give when someone plays Favor on you.
        
        You MUST give them a card - you choose which one.
        
        Args:
            view: Current game state (view.my_hand has your cards)
            requester_id: The player who's asking for a card
        
        Returns:
            A Card from your hand to give away
        
        STRATEGY TIP: Give away your least valuable cards!
                      Keep Defuse and Nope cards if possible.
        """
        
        hand = list(view.my_hand)
        
        # Priority: Keep valuable cards, give away junk
        # 1. Try to give a cat card (useless alone)
        cat_cards = [c for c in hand if "Cat" in c.card_type]
        if cat_cards:
            return random.choice(cat_cards)
        
        # 2. Give anything that's NOT Defuse or Nope
        safe_to_give = [c for c in hand if c.card_type not in ("DefuseCard", "NopeCard")]
        if safe_to_give:
            return random.choice(safe_to_give)
        
        # 3. Last resort: give something (can't keep it)
        return random.choice(hand)
