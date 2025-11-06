# Contributing to Exploding Kitten Bot Battle

Thank you for your interest in creating a bot for the Exploding Kitten Bot Battle! This guide will help you create an effective bot.

## Quick Start

1. Create a new file in `bots/` directory (e.g., `MyAwesomeBot.py`)
2. Copy the template below
3. Implement your strategy
4. Test your bot: `python3 main.py --test`

## Bot Template

```python
"""My awesome bot for Exploding Kittens."""

from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType, TargetContext, GameAction


class MyAwesomeBot(Bot):
    """Description of your bot's strategy."""

    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        """
        Decide which card to play.
        Called repeatedly until you return None.
        """
        # Example: Play Skip if deck is dangerous
        if self._is_deck_dangerous(state):
            for card in self.hand:
                if card.card_type == CardType.SKIP:
                    return card
        
        # Example: Use See the Future to gather info
        for card in self.hand:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card
        
        # No card to play
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        """
        Decide where to put the Exploding Kitten.
        0 = top, state.cards_left_to_draw = bottom
        """
        # Put it at the bottom to be safe
        return state.cards_left_to_draw

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """
        Called when you play See the Future.
        Use this to remember what's coming.
        """
        # You could store this information in instance variables
        # for use in other methods
        pass
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        """
        Choose a target for Favor or combo.
        """
        return alive_players[0] if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        """
        Choose a card to give away (for Favor).
        """
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        """
        Request a specific card type (for 3-of-a-kind combo).
        """
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        """
        Choose a card from discard pile (for 5-unique combo).
        """
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        """
        Decide whether to nope an action.
        
        Args:
            state: Current game state
            action: The action being played (GameAction object with details)
        """
        return False
    
    def on_action_played(self, state: GameState, action: GameAction, actor: 'Bot') -> None:
        """
        Called when any action occurs in the game.
        Track actions for better decision making.
        
        Args:
            state: Current game state
            action: The action that was played
            actor: The bot who played the action
        """
        pass
    
    def _is_deck_dangerous(self, state: GameState) -> bool:
        """Helper method to assess danger."""
        if state.was_last_card_exploding_kitten:
            return True
        # Add more logic here
        return False
```

## Strategy Tips

### Information Gathering

1. **Use See the Future wisely**
   - Play it early to know what's safe
   - Remember what you saw across turns
   - Use it before making big decisions

2. **Track played cards**
   - Use `state.history_of_played_cards` to know what's left
   - Calculate probabilities of drawing Exploding Kittens
   - Track how many Defuse cards have been used

### Defensive Strategies

1. **Skip card usage**
   - Skip when you know an Exploding Kitten is on top
   - Skip when probability of danger is high
   - Don't skip unnecessarily (you need cards!)

2. **Defuse management**
   - You start with 1 Defuse - use it wisely
   - If you draw more, you have more safety margin
   - Consider your Defuse count when taking risks

3. **Exploding Kitten placement**
   - Bottom: Safe but predictable
   - Middle: Balances safety and strategy
   - Top: Aggressive - threatens next player

### Offensive Strategies

1. **Attack cards**
   - Forces next player to take 2 turns
   - Increases their risk of drawing Exploding Kitten
   - Use when deck is dangerous

2. **Shuffle cards**
   - Disrupts other players' plans
   - Use after seeing future if it's bad
   - Randomizes Exploding Kitten positions

3. **Aggressive Exploding Kitten placement**
   - Place near top to threaten opponents
   - Consider if they likely have Defuse
   - Risky but can eliminate players quickly

## Advanced Techniques

### Probability Calculation

```python
def _calculate_explosion_risk(self, state: GameState) -> float:
    """Calculate probability of drawing Exploding Kitten."""
    if state.cards_left_to_draw == 0:
        return 0.0
    
    # Count Exploding Kittens in play
    total_kittens = state.initial_card_counts.get(CardType.EXPLODING_KITTEN, 0)
    played_kittens = sum(
        1 for card in state.history_of_played_cards 
        if card.card_type == CardType.EXPLODING_KITTEN
    )
    remaining_kittens = total_kittens - played_kittens
    
    # Probability = remaining kittens / cards left
    return remaining_kittens / state.cards_left_to_draw
```

### State Tracking

```python
from game import Bot, GameState, Card, GameAction, ActionType

class SmartBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.last_seen_future = []
        self.known_top_cards = []
        self.actions_log = []  # Track all game actions
    
    def on_action_played(self, state: GameState, action: GameAction, actor: 'Bot') -> None:
        """
        Called whenever ANY action happens in the game.
        Override this to track game actions for better decision making.
        
        Args:
            state: Current game state
            action: The action that occurred (GameAction object)
            actor: The bot who performed the action
        """
        # Store action for analysis
        self.actions_log.append({
            'action_type': action.action_type,
            'player': action.player,
            'actor': actor.name,
            'cards_left': state.cards_left_to_draw
        })
        
        # Track if someone drew an Exploding Kitten
        if action.action_type == ActionType.EXPLODING_KITTEN_DRAW:
            # Someone hit a kitten - update your strategy
            pass
    
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        """Store what we saw for later use."""
        self.last_seen_future = top_three.copy()
        self.known_top_cards = top_three.copy()
```

**Benefits of tracking actions:**
- Know when opponents draw/play certain cards
- Track when Exploding Kittens are drawn/defused
- Infer opponent strategies from their actions
- Make better Nope decisions based on who's being targeted

### Adaptive Strategy

```python
def play(self, state: GameState) -> Optional[Card]:
    """Adapt strategy based on game state."""
    # Early game: gather information
    if state.alive_bots > 3:
        return self._early_game_strategy(state)
    
    # Late game: be more aggressive
    else:
        return self._late_game_strategy(state)
```

## Testing Your Bot

1. **Test against itself**
   ```bash
   # Only have your bot in bots/ directory
   python3 main.py --test
   ```

2. **Test against example bots**
   ```bash
   # Include your bot + example bots
   python3 main.py --test
   ```

3. **Run multiple times**
   ```bash
   # Create a test script
   for i in {1..10}; do python3 main.py --test; done
   ```

## Common Mistakes

1. **Playing cards you don't have**
   - Always check with `self.has_card()` or `self.has_card_type()`
   - The game will catch this and end your turn

2. **Infinite loops in play()**
   - Always return None at some point
   - Don't play all your cards every turn

3. **Not using game state information**
   - `state` parameter has valuable info
   - Use it to make informed decisions

4. **Using Defuse or Exploding Kitten in combos**
   - Defuse cards cannot be used in any combos
   - Exploding Kitten cards cannot be used in any combos
   - The game will reject such combos as invalid
   
   ```python
   # ❌ BAD - Trying to combo with DEFUSE
   defuse_cards = [c for c in self.hand if c.card_type == CardType.DEFUSE]
   if len(defuse_cards) >= 2:
       return defuse_cards[:2]  # Invalid combo!
   
   # ✅ GOOD - Only combo with valid cards
   attack_cards = [c for c in self.hand if c.card_type == CardType.ATTACK]
   if len(attack_cards) >= 2:
       return attack_cards[:2]  # Valid combo
   ```

5. **Forgetting about edge cases**
   - What if deck is empty?
   - What if you have no playable cards?
   - What if you're the last player?

## Bot Examples

### Minimal Bot (Just Survives)
```python
from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType, TargetContext, GameAction

class MinimalBot(Bot):
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        return None  # Never play cards
    
    def handle_exploding_kitten(self, state: GameState) -> int:
        return state.cards_left_to_draw  # Always bottom
    
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        pass  # Ignore the information
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        return alive_players[0] if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        return False  # Never nope
    
    def on_action_played(self, state: GameState, action: GameAction, actor: 'Bot') -> None:
        pass  # Don't track actions
```

### Information-Based Bot
```python
from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType, TargetContext, GameAction

class InfoBot(Bot):
    def __init__(self, name: str):
        super().__init__(name)
        self.future_cards = []
    
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        # Always use See the Future if available
        for card in self.hand:
            if card.card_type == CardType.SEE_THE_FUTURE:
                return card
        
        # Skip if we know Exploding Kitten is on top
        if self.future_cards and self.future_cards[0].card_type == CardType.EXPLODING_KITTEN:
            for card in self.hand:
                if card.card_type == CardType.SKIP:
                    return card
        
        return None
    
    def handle_exploding_kitten(self, state: GameState) -> int:
        return state.cards_left_to_draw
    
    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        self.future_cards = top_three.copy()
    
    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        return alive_players[0] if alive_players else None
    
    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        return self.hand[0] if self.hand else None
    
    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        return CardType.DEFUSE
    
    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        return discard_pile[0] if discard_pile else None
    
    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        return False
    
    def on_action_played(self, state: GameState, action: GameAction, actor: 'Bot') -> None:
        pass
```

## Debugging Tips

1. **Add print statements**
   ```python
   def play(self, state: GameState) -> Optional[Card]:
       print(f"{self.name}: I have {len(self.hand)} cards")
       # ... your logic
   ```

2. **Check your bot is loaded**
   ```bash
   python3 main.py --test | head -10
   # Should show "Loaded bot: YourBotName"
   ```

3. **Verify class name matches file name**
   - File: `MyBot.py`
   - Class: `class MyBot(Bot):`

## Testing Your Bot

### Single Game Testing
Run a single game to see how your bot behaves:
```bash
python3 main.py --test
```

This mode:
- Shows detailed output of each turn
- Displays all card plays and decisions
- Useful for debugging strategy

### Performance Testing with Statistics
Evaluate your bot's performance over many games:
```bash
# Display statistics in console only
python3 main.py --stats --runs 100

# Display statistics AND save to a file
python3 main.py --stats my_bot_stats.json --runs 100

# Run with parallel processing for faster results (recommended for large runs)
python3 main.py --stats --runs 10000 --parallel

# Parallel mode with file output for extensive testing
python3 main.py --stats extensive_test.json --runs 100000 --parallel
```

This mode:
- Runs 100 games automatically (or specify with `--runs N`)
- **NEW: Parallel execution** with `--parallel` flag for ~1.7x speedup on multi-core systems
- Minimal console output for speed
- Shows progress every 10 games
- Displays comprehensive statistics in the console
- Optionally saves statistics to a JSON file (if filename provided)

**Example output:**
```
Running 100 games for statistics...
Progress: 10/100 games completed (10.0%)
Progress: 20/100 games completed (20.0%)
...
Progress: 100/100 games completed (100.0%)

STATISTICS SUMMARY - 100 games played

MyBot:
  Wins: 42/100 (42.0%)
  Average Placement: 1.85
  Placement Distribution:
    1st   :  42 ( 42.0%) █████████████████████
    2nd   :  31 ( 31.0%) ███████████████
    3rd   :  27 ( 27.0%) █████████████
```

**What to look for in statistics:**
- **Win Rate**: Higher is better (33.3% is average for 3 bots)
- **Average Placement**: Lower is better (1.0 = always wins)
- **Placement Distribution**: Should see more 1st place finishes than 2nd/3rd

**Comparing bots:**
Run statistics mode with multiple bots to compare strategies:
```bash
# Make sure your bot file is in bots/ directory
ls bots/
# MyBot.py  AggressiveBot.py  CautiousBot.py  RandomBot.py

# Just display results
python3 main.py --stats --runs 200

# Or save to file for later analysis
python3 main.py --stats comparison.json --runs 200

# For robust comparison, use parallel mode with many games
python3 main.py --stats robust_comparison.json --runs 50000 --parallel
```

When saved, the statistics file contains detailed JSON data for further analysis.

**Performance Tip:** For runs with 1,000+ games, use the `--parallel` flag to leverage multiple CPU cores and reduce execution time by approximately 40-70% depending on your system.

## Have Fun!

Remember, this is a learning exercise and a fun competition. Try different strategies, learn from failures, and iterate on your design. Good luck! 🎮
