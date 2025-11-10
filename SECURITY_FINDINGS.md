# Bot Cheating Investigation - Security Findings

## Executive Summary

This document outlines potential cheating vulnerabilities in the Exploding Kitten Bot Battle game and proposes prevention measures.

## Investigation Date
2025-11-10

## Potential Cheating Vectors Identified

### 1. **Direct Hand Manipulation (CRITICAL)**
**Vulnerability:** Bots have direct access to `self.hand` list which is mutable.

**How bots could cheat:**
```python
# In any bot method
def play(self, state: GameState):
    # CHEAT: Add cards to hand without drawing
    self.hand.append(Card(CardType.DEFUSE))
    self.hand.append(Card(CardType.SKIP))
    return None
```

**Current Protection:** None - bots can modify `self.hand` directly.

**Risk Level:** HIGH - Allows arbitrary card addition without any game mechanics.

---

### 2. **GameState Modification (MEDIUM)**
**Vulnerability:** While GameState is passed via `.copy()`, the copy is shallow for complex objects.

**How bots could cheat:**
```python
def play(self, state: GameState):
    # Modifying the copy doesn't affect the game (good)
    # But lists inside are shallow copies
    state.history_of_played_cards.append(Card(CardType.SKIP))
    # This DOES modify the original game state!
```

**Current Protection:** Partial - `.copy()` creates new GameState but lists are shallow copied.

**Risk Level:** MEDIUM - Can potentially corrupt game state tracking.

---

### 3. **Playing Cards Not in Hand (LOW)**
**Vulnerability:** Bots could return cards they don't possess.

**How bots could cheat:**
```python
def play(self, state: GameState):
    # Try to play a card not in hand
    return Card(CardType.DEFUSE)
```

**Current Protection:** YES - Game engine validates with `bot.has_card(play_result)` at line 461.

**Risk Level:** LOW - Already protected by validation in `_play_phase`.

---

### 4. **Invalid Combo Attempts (LOW)**
**Vulnerability:** Bots could try to play invalid combos with cards they don't have.

**How bots could cheat:**
```python
def play(self, state: GameState):
    # Try to play combo with cards not in hand
    return [Card(CardType.DEFUSE), Card(CardType.DEFUSE)]
```

**Current Protection:** YES - Game engine validates all cards in combo at line 494-498.

**Risk Level:** LOW - Already protected by validation in `_handle_combo`.

---

### 5. **Exploding Kitten Prevention (CRITICAL)**
**Vulnerability:** Bots could manipulate their alive status or add Defuse cards during explosion.

**How bots could cheat:**
```python
def handle_exploding_kitten(self, state: GameState):
    # CHEAT: Add defuse card when we don't have one
    self.hand.append(Card(CardType.DEFUSE))
    return 0
    
# Or in draw phase:
def on_action_played(self, state, action, actor):
    if action.action_type == ActionType.EXPLODING_KITTEN_DRAW and action.player == self.name:
        # CHEAT: Add defuse after drawing exploding kitten
        self.hand.append(Card(CardType.DEFUSE))
```

**Current Protection:** None - The defuse check happens at line 816 but bot could add cards between draw and check.

**Risk Level:** HIGH - Allows bots to avoid elimination.

---

### 6. **Stealing from Other Bots (CRITICAL)**
**Vulnerability:** Bots have references to other Bot objects and could directly manipulate them.

**How bots could cheat:**
```python
def choose_target(self, state: GameState, alive_players: List[Bot], context):
    # CHEAT: Steal cards from all opponents
    for bot in alive_players:
        while bot.hand:
            card = bot.hand.pop()
            self.hand.append(card)
    return alive_players[0] if alive_players else None
```

**Current Protection:** None - Bots receive direct references to other Bot objects.

**Risk Level:** CRITICAL - Allows direct theft without game mechanics.

---

### 7. **Deck Manipulation (CRITICAL if exposed)**
**Vulnerability:** If bots gain access to the Deck object, they could manipulate it.

**How bots could cheat (if they had access):**
```python
# If bot somehow gets deck reference
deck.draw_pile.clear()  # Remove all exploding kittens
deck.draw_pile = [Card(CardType.SKIP)] * 100  # Fill with safe cards
```

**Current Protection:** YES - Deck is NOT passed to bots, only GameEngine has access.

**Risk Level:** LOW - Bots don't have access to Deck object.

---

### 8. **GameEngine State Manipulation (LOW)**
**Vulnerability:** If bots gain access to GameEngine, they could modify game rules.

**Current Protection:** YES - GameEngine is not passed to bots.

**Risk Level:** LOW - Bots don't have access to GameEngine object.

---

## Summary of Vulnerabilities

### Critical Issues (Must Fix):
1. **Direct hand manipulation** - Bots can add cards to `self.hand` 
2. **Stealing from other bots** - Bots receive references to other Bot objects
3. **Exploding kitten prevention** - Bots can add Defuse cards during explosion handling

### Medium Issues (Should Fix):
1. **GameState shallow copy** - Lists inside GameState are shallow copied

### Protected (Already Safe):
1. Playing cards not in hand - Validated by game engine
2. Invalid combos - Validated by game engine
3. Deck access - Not exposed to bots
4. GameEngine access - Not exposed to bots

---

## Proposed Prevention Measures

### 1. Make Bot Hands Private and Controlled
**Change:** Make `self.hand` private and provide controlled access.

```python
class Bot(ABC):
    def __init__(self, name: str):
        self.name = name
        self._hand: List[Card] = []  # Private
        self.alive = True
    
    @property
    def hand(self) -> List[Card]:
        """Read-only view of hand."""
        return self._hand.copy()  # Return copy to prevent modification
    
    # Only game engine can modify hand via these methods
    def _add_card_internal(self, card: Card) -> None:
        """Internal method for game engine only."""
        self._hand.append(card)
    
    def _remove_card_internal(self, card: Card) -> bool:
        """Internal method for game engine only."""
        if card in self._hand:
            self._hand.remove(card)
            return True
        return False
```

**Impact:** Bots can't directly modify hand, must use game mechanics.

---

### 2. Make GameState Fully Immutable
**Change:** Deep copy all nested structures and make GameState frozen.

```python
@dataclass(frozen=True)
class GameState:
    initial_card_counts: Dict[CardType, int]
    cards_left_to_draw: int
    was_last_card_exploding_kitten: bool
    history_of_played_cards: tuple[Card, ...]  # Immutable tuple
    alive_bots: int

    def copy(self) -> 'GameState':
        """Create a deep copy of the game state."""
        return GameState(
            initial_card_counts=self.initial_card_counts.copy(),
            cards_left_to_draw=self.cards_left_to_draw,
            was_last_card_exploding_kitten=self.was_last_card_exploding_kitten,
            history_of_played_cards=tuple(self.history_of_played_cards),
            alive_bots=self.alive_bots,
        )
```

**Impact:** Bots cannot modify game state tracking.

---

### 3. Pass Bot Proxies Instead of Real Bots
**Change:** Create read-only proxy objects for bots when selecting targets.

```python
class BotProxy:
    """Read-only proxy for Bot objects."""
    def __init__(self, bot: Bot):
        self._bot = bot
        self.name = bot.name
        self.alive = bot.alive
        # Don't expose hand or any methods that modify state
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"BotProxy({self.name})"
```

**Impact:** Bots can't directly manipulate other bots.

---

### 4. Validate Hand State at Critical Points
**Change:** Add validation before and after bot method calls.

```python
def _validate_bot_hand(self, bot: Bot, expected_size: int = None) -> bool:
    """Validate that bot's hand hasn't been tampered with."""
    if expected_size is not None and len(bot.hand) != expected_size:
        self._log(f"WARNING: {bot.name}'s hand size changed unexpectedly!")
        return False
    return True

def _draw_phase(self, bot: Bot) -> None:
    hand_size_before = len(bot.hand)
    # ... existing code ...
    # After explosion handling
    if not bot.alive:
        # Validate dead bot didn't add cards
        if len(bot.hand) != hand_size_before:
            self._log(f"CHEAT DETECTED: {bot.name} modified hand after elimination!")
            bot.hand = bot.hand[:hand_size_before]  # Revert changes
```

**Impact:** Detect and prevent cheating attempts.

---

### 5. Sandbox Bot Execution (Advanced)
**Change:** Run bot methods in restricted environment.

**Note:** This is complex and may not be necessary if other measures are implemented.

---

## Implementation Priority

### Phase 1 (High Priority - Must Fix):
1. ✅ Document all vulnerabilities (this document)
2. 🔨 Create comprehensive cheat tests
3. 🔨 Make bot hands private and controlled
4. 🔨 Pass BotProxy objects instead of real bots
5. 🔨 Add hand validation at critical points

### Phase 2 (Medium Priority - Should Fix):
1. 🔨 Make GameState fully immutable with frozen dataclass
2. 🔨 Deep copy nested structures in GameState

### Phase 3 (Nice to Have):
1. Add audit logging for suspicious behavior
2. Consider sandboxing bot execution

---

## Testing Strategy

### Test Coverage:
1. ✅ Test that bots cannot add cards to hand directly
2. ✅ Test that bots cannot steal from other bots
3. ✅ Test that bots cannot prevent explosion without defuse
4. ✅ Test that GameState modifications don't affect game
5. ✅ Test that invalid card plays are rejected
6. ✅ Test that invalid combos are rejected

---

## Conclusion

The current implementation has several **critical security vulnerabilities** that allow bots to cheat by:
1. Adding cards to their hand without drawing
2. Stealing cards directly from other bots
3. Avoiding elimination by adding Defuse cards during explosion

**Recommended Action:** Implement Phase 1 prevention measures immediately to ensure fair gameplay.

---

## Notes

- All proposed changes maintain backward compatibility with existing bot implementations
- Changes focus on making the game engine more defensive
- Bot interface remains the same from bot developer perspective
- Only internal implementation details change for security
