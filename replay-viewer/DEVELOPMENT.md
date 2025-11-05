# Replay Viewer Development Guide

This document contains detailed information about the replay viewer's architecture, common pitfalls, edge cases, and lessons learned during development.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Asynchronous Event Processing](#asynchronous-event-processing)
3. [Common Pitfalls and Edge Cases](#common-pitfalls-and-edge-cases)
4. [Testing Challenges](#testing-challenges)
5. [Lessons Learned](#lessons-learned)

## Architecture Overview

### Core Components

- **`main.ts`**: Application entry point, UI management, and event coordination
- **`replayPlayer.ts`**: Manages replay state, playback control, and event progression
- **`visualRenderer.ts`**: Handles visual rendering and game state display
- **`animationController.ts`**: Manages card animations and transitions
- **`gameBoard.ts`**: DOM manipulation for the game board layout

### Event Flow

```
User Action → main.ts → replayPlayer.ts → Event Callbacks → main.ts (updateDisplay) → visualRenderer.ts → animationController.ts → DOM
```

## Asynchronous Event Processing

### The Processing Flag Pattern

The replay viewer uses an `isProcessingEvent` flag to prevent concurrent event processing. This is critical for maintaining state consistency.

#### Key Implementation Details

1. **Flag Lifecycle**:
   ```typescript
   // In updateDisplay()
   while (this.isProcessingEvent) {
     await this.delay(10); // Wait for previous processing to complete
   }
   this.isProcessingEvent = true;
   try {
     // Process event
   } finally {
     this.isProcessingEvent = false; // Always clear in finally block
   }
   ```

2. **Counter Update Timing**:
   - The event counter MUST be updated in the `finally` block
   - The counter MUST be updated AFTER `isProcessingEvent` is set to false
   - This ensures Playwright tests see the counter only when the system is ready

3. **Why This Matters**:
   - If the counter updates before the flag is cleared, tests will see the new counter value but clicks will be blocked
   - This causes intermittent test failures where the second/third click doesn't work

### Multiple Callbacks and Race Conditions

The replay player uses a callback pattern for event notifications:

```typescript
this.player.onEventChange(async (_event, index) => {
  await this.updateDisplay(index);
});
```

**Important**: Only ONE callback should be registered for event changes. Multiple callbacks would cause:
- Multiple concurrent calls to `updateDisplay()`
- Race conditions with the `isProcessingEvent` flag
- Inconsistent UI state

## Common Pitfalls and Edge Cases

### 1. Early Returns in Try Blocks

**Problem**: Early returns inside a try block still execute the finally block, but the state may be inconsistent.

```typescript
// PROBLEMATIC
try {
  const data = getData();
  if (!data) return; // Finally still executes!
  
  processData(data);
  updateUI(); // This is in the try block
} finally {
  clearFlag();
  updateCounter(); // This always runs, even if we returned early!
}
```

**Solution**: Use a flag to track whether processing completed successfully:

```typescript
let shouldUpdateCounter = false;
try {
  const data = getData();
  if (!data) return;
  
  processData(data);
  shouldUpdateCounter = true; // Only set if we got here
} finally {
  clearFlag();
  if (shouldUpdateCounter) {
    updateCounter();
  }
}
```

### 2. Animation Timing and isAnimating Flag

The `visualRenderer` maintains its own `isAnimating` flag that's separate from `isProcessingEvent`.

**Key Points**:
- `isAnimating` is set at the start of `renderEvent()` and cleared in its finally block
- `isProcessingEvent` wraps the entire event processing including the render
- Both flags must be false before accepting new input
- The order is: `isProcessingEvent = true` → `isAnimating = true` → animations → `isAnimating = false` → `isProcessingEvent = false`

### 3. File Loading Synchronization

**Problem**: The file input's `change` event handler is async, but event listeners don't await async handlers.

```typescript
// Event listener doesn't await!
fileInput.addEventListener("change", (e) => this.handleFileLoad(e));
```

**Solution**: Ensure UI elements that indicate "ready" state (like showing playback controls) only appear AFTER all async initialization completes:

```typescript
async handleFileLoad(e: Event) {
  // Load and parse file
  // Initialize renderer
  // Process first event
  await this.updateDisplay(0); // Wait for this!
  
  // Only NOW show the controls
  showControls();
}
```

### 4. Button State Management

**Problem**: Disabling a button doesn't prevent Playwright from clicking it.

**Solution**: Use both disabled state AND processing flags:

```typescript
async stepForward() {
  if (this.isProcessingEvent) return; // Guard clause
  
  button.disabled = true; // Visual feedback
  try {
    await doWork();
  } finally {
    button.disabled = false; // Re-enable
  }
}
```

Tests should wait for the button to be enabled:
```typescript
await button.click();
await expect(button).toBeEnabled(); // Wait for re-enable
```

### 5. Event Index vs Display Number

**Critical Understanding**: 
- Event indices are 0-based in code
- Display shows 1-based numbering for users
- Event 0 (index) = "Event: 1 / 123" (display)
- Event 1 (index) = "Event: 2 / 123" (display)

**Common Bug**: Mixing up indices when debugging. Always check if you're working with the internal index or the display number.

### 6. Combo Play Events and Animations

**Important**: A single `combo_play` event in the replay file may trigger multiple card animations.

```json
{
  "type": "combo_play",
  "cards": ["NOPE", "NOPE"]  // 2 cards, but ONE event
}
```

The frontend will:
1. Receive ONE `combo_play` event (index N)
2. Animate each card sequentially
3. Update counter to N+1 once ALL cards are animated
4. The counter does NOT increment for each card - just once for the whole combo

This is correct behavior! The replay file represents logical game events, not individual animations.

## Testing Challenges

### Playwright Test Timing Issues

#### The Multiple Step Forward Problem

**Issue**: Tests that rapidly click the step forward button multiple times often fail on the second or third click.

**Root Cause**: 
1. Playwright's `click()` doesn't wait for async event handlers to complete
2. The test sees the counter update and immediately clicks again
3. But the processing flag might still be true, blocking the next step
4. Even with proper flag management, rapid clicks can create race conditions

**Solution Options**:

1. **Wait for button to be enabled** (partial solution):
   ```typescript
   await stepButton.click();
   await expect(eventCounter).toContainText('Event: 2 /');
   await expect(stepButton).toBeEnabled(); // Add this
   ```

2. **Use jump functionality instead** (better solution):
   ```typescript
   // Instead of multiple step clicks
   await stepButton.click(); // Get to event 2
   await agentJumpInput.evaluate(el => {
     el.value = '5';
     el.dispatchEvent(new Event('input'));
   }); // Jump to event 6
   ```

3. **Add explicit delays** (not recommended):
   ```typescript
   await stepButton.click();
   await page.waitForTimeout(100); // Brittle!
   ```

#### Why Jump Works Better Than Multiple Steps

The jump functionality:
- Processes all intermediate events silently (no animations)
- Sets the flag once at the start
- Updates the counter once at the end
- Avoids the multiple click timing issues
- Is faster for tests

### Test-Specific Considerations

1. **Always wait for the counter to update**, not just the button state
2. **Use `timeout` parameters** for expects: `expect(element).toContainText('...', { timeout: 2000 })`
3. **Test one thing at a time**: Don't combine testing step forward with testing other features
4. **Use data attributes** for debugging: `data-current-index` helps verify internal state
5. **Check console output**: The app logs errors to the console, capture them in tests

## Lessons Learned

### 1. Asynchronous State Management is Hard

Managing async state in a UI with animations requires careful coordination:
- Multiple flags for different states (`isProcessingEvent`, `isAnimating`)
- Proper use of `finally` blocks to guarantee cleanup
- Understanding microtask queues and event loop timing

### 2. Finally Blocks Always Execute

Even if you return early in a try block, the finally block runs. This means:
- ✅ Good for cleanup (clearing flags)
- ❌ Bad for conditional updates (use a flag to track success)

### 3. Playwright Doesn't Wait for Async Handlers

When you click a button with an async handler, Playwright's `click()` returns immediately:
```typescript
// This doesn't wait for stepForward() to complete!
button.addEventListener('click', () => this.stepForward());
await page.click('#button'); // Returns immediately
```

You must explicitly wait for the side effects (counter update, button re-enable, etc.)

### 4. Race Conditions Are Subtle

The race condition where the counter updates before the flag is cleared is a perfect example:
- It works 99% of the time in manual testing
- It fails intermittently in automated tests
- The fix is moving ONE line (counter update) from try to finally block

### 5. Test What You're Testing

The original test was named "should not jump backward" but it was actually testing:
1. Step forward 3 times (test setup)
2. Jump backward (actual test)

When step forward failed, it looked like jump backward was broken. Better approach:
- Use jump to set up state for jump backward test
- Keep step forward tests separate
- Each test should have one clear purpose

### 6. DOM Updates Are Synchronous, But Callbacks Aren't

```typescript
// This updates the DOM immediately
element.textContent = "New value";

// But this callback runs asynchronously
await Promise.all(callbacks.map(cb => cb()));
```

Playwright can see DOM changes before your async processing completes!

### 7. Event Counters and Indices Need Clear Documentation

The confusion between 0-based indices and 1-based display numbers caused multiple bugs during development. Document this clearly in code comments and user-facing documentation.

### 8. Wait Loops vs Early Returns

For mutual exclusion, wait loops are better than early returns:

```typescript
// Early return (can lose events)
if (this.isProcessing) return;

// Wait loop (queues events)  
while (this.isProcessing) await delay(10);
```

The wait loop ensures events aren't dropped, just delayed.

## Best Practices

1. **Always use finally blocks** for cleanup
2. **Update UI in finally blocks** after clearing processing flags
3. **Use wait loops** instead of early returns for async mutual exclusion
4. **Track success** with a flag if you have early returns
5. **Document timing** assumptions in comments
6. **Test async flows** thoroughly, they're the source of most bugs
7. **Use the jump functionality** for test setup, not rapid step clicks
8. **Add data attributes** for testing/debugging internal state
9. **Keep event callbacks simple** - one callback per event type
10. **Clear comments** about why timing/order matters

## Debugging Tips

1. **Add data attributes** to track internal state:
   ```typescript
   element.setAttribute('data-processing', String(isProcessing));
   ```

2. **Use console.log with prefixes**:
   ```typescript
   console.log('[stepForward] Starting step');
   ```

3. **Capture console logs in tests**:
   ```typescript
   page.on('console', msg => console.log('BROWSER:', msg.text()));
   ```

4. **Check timing** with delays:
   ```typescript
   await this.delay(100);
   console.log('After delay, flag is:', this.isProcessingEvent);
   ```

5. **Use Playwright's trace viewer**:
   ```bash
   npx playwright test --trace on
   npx playwright show-trace trace.zip
   ```

6. **Simplify the test** to isolate the issue:
   - Remove all but the failing assertion
   - Add explicit waits
   - Check intermediate state

## Future Improvements

Potential areas for enhancement:

1. **Event Queue**: Instead of blocking with `isProcessingEvent`, queue events and process them sequentially
2. **Promise-based API**: Return promises from UI actions so tests can await them
3. **Better State Machine**: Use a formal state machine instead of boolean flags
4. **Retry Logic**: Add automatic retry for failed animations
5. **Performance Metrics**: Track and log timing for debugging
6. **Isolated Testing**: Unit test individual components in isolation

## Conclusion

The replay viewer's async architecture requires careful attention to:
- Flag management and cleanup
- Timing of UI updates
- Test synchronization
- Clear documentation of event flow

Most bugs in this codebase relate to async timing, race conditions, and the interaction between event processing and UI updates. Understanding the full event flow and flag lifecycle is critical for maintaining and extending the code.
