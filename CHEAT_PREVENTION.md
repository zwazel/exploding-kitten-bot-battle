# Bot Cheat Prevention - Developer Guide

## Overview

The Exploding Kitten Bot Battle game includes cheat prevention mechanisms to ensure fair gameplay. This document explains how these protections work and what it means for bot developers.

## Key Protection: BotProxy

When your bot needs to choose a target (for Favor cards or combos), you receive `BotProxy` objects instead of direct `Bot` references.

### What is BotProxy?

BotProxy is a read-only wrapper around Bot objects that prevents bots from directly manipulating other bots' hands or state.

### What You Can Access

```python
def choose_target(self, state: GameState, alive_players: List[BotProxy], context: TargetContext) -> Optional[BotProxy]:
    if not alive_players:
        return None
    
    target = alive_players[0]
    
    # ✅ ALLOWED: Read the bot's name
    name = target.name
    
    # ✅ ALLOWED: Check if bot is alive
    is_alive = target.alive
    
    # ✅ ALLOWED: Get hand size for decision-making
    hand_size = len(target.hand)  # Returns integer
    
    # ✅ ALLOWED: Compare bots
    biggest_hand = max(alive_players, key=lambda b: len(b.hand))
    
    return target
```

### What You Cannot Do

```python
def choose_target(self, state: GameState, alive_players: List[BotProxy], context: TargetContext) -> Optional[BotProxy]:
    target = alive_players[0]
    
    # ❌ BLOCKED: Cannot see actual cards in hand
    # target.hand contains None values, not actual Card objects
    first_card = target.hand[0]  # Returns None
    
    # ❌ BLOCKED: Cannot steal cards directly
    # Even if you try, you'll get None values
    for card in target.hand:
        self.hand.append(card)  # Adds None, not actual cards
    
    # ❌ BLOCKED: Cannot modify other bot's hand
    target.hand.append(Card(CardType.DEFUSE))  # Affects fake list only
    
    # ❌ BLOCKED: Cannot access other methods
    # target.play()  # AttributeError: BotProxy has no attribute 'play'
    
    return target
```

## Best Practices

### ✅ DO:

1. **Use hand size for targeting decisions:**
   ```python
   # Target the player with the most cards
   return max(alive_players, key=lambda b: len(b.hand))
   ```

2. **Compare bots by name:**
   ```python
   # Track which bot you targeted last
   if target.name == self.last_target:
       # Choose someone else
       pass
   ```

3. **Check if bot is alive:**
   ```python
   # Filter out dead bots (though game engine already does this)
   alive = [b for b in alive_players if b.alive]
   ```

### ❌ DON'T:

1. **Try to access individual cards:**
   ```python
   # ❌ BAD: Will only get None values
   for card in target.hand:
       if card.card_type == CardType.DEFUSE:  # AttributeError!
           return target
   ```

2. **Try to modify other bots:**
   ```python
   # ❌ BAD: Doesn't affect the real bot
   target.hand.clear()
   ```

3. **Assume you can call bot methods:**
   ```python
   # ❌ BAD: BotProxy doesn't expose methods
   target.play(state)  # AttributeError!
   ```

## Migration from Old Code

If you have existing bot code that worked before BotProxy, it should continue to work if you only used `len(bot.hand)`:

### Before (Still Works):
```python
def choose_target(self, state, alive_players, context):
    # This pattern still works!
    return max(alive_players, key=lambda b: len(b.hand))
```

### Before (Needs Update):
```python
def choose_target(self, state, alive_players, context):
    # This won't work anymore - can't see actual cards
    for bot in alive_players:
        if any(c.card_type == CardType.DEFUSE for c in bot.hand):
            return bot  # ❌ Won't work as expected
    return alive_players[0]
```

### After (Fixed):
```python
def choose_target(self, state, alive_players, context):
    # Use hand size or name for decisions instead
    return max(alive_players, key=lambda b: len(b.hand))
```

## Why This Protection?

Without BotProxy, malicious bots could:
- Steal cards directly from opponents
- See opponents' entire hands
- Modify opponents' cards or state
- Cheat the game mechanics

With BotProxy:
- Bots can only see public information (name, alive status, hand size)
- Cannot access or modify actual cards
- Cannot call methods on other bots
- Game remains fair and balanced

## GameState Protection

GameState is also protected from modifications:

```python
def play(self, state: GameState):
    # ✅ ALLOWED: Read game state
    cards_left = state.cards_left_to_draw
    history_length = len(state.history_of_played_cards)
    
    # ❌ BLOCKED: Cannot modify history (it's a tuple)
    # state.history_of_played_cards.append(card)  # AttributeError!
    
    # ⚠️ INEFFECTIVE: Modifying copy doesn't affect game
    state.cards_left_to_draw = 0  # Only affects your copy
    
    return None
```

The `history_of_played_cards` is an immutable tuple, preventing corruption of game state tracking.

## Summary

- **BotProxy** prevents bots from cheating by restricting access to other bots
- You can still use `len(bot.hand)` for targeting decisions
- You cannot see or steal individual cards from other bots
- All existing bots that used `len(bot.hand)` continue to work
- These protections ensure fair gameplay for all participants

## Questions?

If you have questions about these protections or need help updating your bot, please refer to:
- `SECURITY_FINDINGS.md` - Complete security analysis
- `CONTRIBUTING.md` - Bot creation guide
- `README.md` - Game rules and API documentation
