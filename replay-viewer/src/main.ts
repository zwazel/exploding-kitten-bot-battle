/**
 * Exploding Kittens Replay Viewer
 * Main application entry point
 */

import "./style.css";
import { ReplayPlayer } from "./replayPlayer";
import { VisualRenderer } from "./visualRenderer";
import type { ReplayData, CardType, ReplayEvent } from "./types";

class ReplayApp {
  private player: ReplayPlayer;
  private renderer!: VisualRenderer;
  private fileInput: HTMLInputElement | null = null;
  private isProcessingEvent = false;
  private readonly MAX_EVENT_PROCESSING_TIMEOUT_MS = 5000;

  constructor() {
    this.player = new ReplayPlayer();
    this.initializeUI();
    this.renderer = new VisualRenderer(
      document.querySelector<HTMLDivElement>("#game-display")!
    );
    this.setupEventListeners();
  }

  private initializeUI(): void {
    const app = document.querySelector<HTMLDivElement>("#app")!;
    app.innerHTML = `
      <div class="replay-viewer">
        <header>
          <h1>🎮 Exploding Kittens Replay Viewer</h1>
        </header>
        
        <div class="controls-panel">
          <div class="file-controls">
            <input type="file" id="file-input" accept=".json" />
            <label for="file-input" class="file-label">📁 Load Replay File</label>
            <span id="file-name" class="file-name"></span>
          </div>
          
          <div class="playback-controls" id="playback-controls" style="display: none;">
            <button id="btn-stop" title="Stop and Reset">⏹️</button>
            <button id="btn-play-pause" title="Play/Pause">▶️</button>
            <button id="btn-step-forward" title="Step Forward">⏭️</button>
            
            <div class="speed-control">
              <label for="speed-slider">Speed:</label>
              <input type="range" id="speed-slider" min="0.5" max="10" step="0.5" value="1" />
              <span id="speed-display">1.0x</span>
              <input type="number" id="speed-input" min="0.1" max="100" step="0.1" value="1.0" title="Custom speed (0.1x - 100x)" />
            </div>
            
            <div class="event-progress">
              <span id="event-counter">Event: 0 / 0</span>
            </div>
            
            <!-- Hidden jump control for automated testing/agents only -->
            <input type="hidden" id="agent-jump-to-event" data-testid="agent-jump-to-event" value="0" />
          </div>
        </div>
        
        <div id="game-display" class="game-display">
          <div class="welcome-message">
            <h2>Welcome to Exploding Kittens Replay Viewer</h2>
            <p>Load a replay JSON file to start viewing the game.</p>
            <p>Watch cards move between players, deck, and discard pile with animated gameplay!</p>
          </div>
        </div>
      </div>
    `;
  }

  private setupEventListeners(): void {
    // File input
    this.fileInput = document.querySelector<HTMLInputElement>("#file-input")!;
    this.fileInput.addEventListener("change", (e) => this.handleFileLoad(e));

    // Playback controls
    document.querySelector("#btn-play-pause")?.addEventListener("click", () => this.togglePlayPause());
    document.querySelector("#btn-stop")?.addEventListener("click", async () => await this.stop());
    document.querySelector("#btn-step-forward")?.addEventListener("click", () => this.stepForward());

    // Speed control - slider
    const speedSlider = document.querySelector<HTMLInputElement>("#speed-slider")!;
    speedSlider.addEventListener("input", (e) => {
      const speed = parseFloat((e.target as HTMLInputElement).value);
      this.player.setSpeed(speed);
      this.updateSpeedDisplay(speed);
    });

    // Speed control - input field
    const speedInput = document.querySelector<HTMLInputElement>("#speed-input")!;
    speedInput.addEventListener("change", (e) => {
      const speed = parseFloat((e.target as HTMLInputElement).value);
      // Clamp the speed between min and max
      const clampedSpeed = Math.max(0.1, Math.min(100, speed));
      this.player.setSpeed(clampedSpeed);
      this.updateSpeedDisplay(clampedSpeed);
      // Update the input field to show the clamped value
      speedInput.value = clampedSpeed.toFixed(1);
    });

    // Hidden agent jump control - only listens to input event (not MutationObserver)
    // MutationObserver won't detect programmatic value property changes, only attribute changes
    // IMPORTANT: When setting the value of this input programmatically (e.g., in tests),
    // you must also dispatch an input event:
    // agentJumpInput.value = "42";
    // agentJumpInput.dispatchEvent(new Event('input', { bubbles: true }));
    // This ensures the application responds to the change as expected.
    const agentJumpInput = document.querySelector<HTMLInputElement>("#agent-jump-to-event")!;
    agentJumpInput.addEventListener("input", () => this.handleAgentJump());

    // Player callbacks
    this.player.onEventChange(async (_event, index) => {
      await this.updateDisplay(index);
    });

    this.player.onStateChange((state) => {
      this.updatePlaybackUI(state);
    });
  }

  private async handleFileLoad(e: Event): Promise<void> {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data: ReplayData = JSON.parse(text);
      
      this.player.loadReplay(data);
      await this.renderer.renderGameSetup(data);

      // Update event counter
      this.updateEventCounter(0, data.events.length);

      // Show first event by triggering event change
      const firstEvent = data.events[0];
      if (firstEvent) {
        await this.updateDisplay(0);
      }

      // Show controls and update UI AFTER initial event is processed
      document.querySelector<HTMLDivElement>("#playback-controls")!.style.display = "flex";
      document.querySelector<HTMLSpanElement>("#file-name")!.textContent = file.name;
    } catch (error) {
      alert(`Error loading replay file: ${error}`);
      console.error("Error loading replay:", error);
    }
  }

  private togglePlayPause(): void {
    const state = this.player.getPlaybackState();
    if (state.isPlaying) {
      this.player.pause();
    } else {
      this.player.play();
    }
  }

  private async stop(): Promise<void> {
    this.player.stop();
    
    // Wait for any ongoing event processing to complete
    while (this.isProcessingEvent) {
      await this.delay(50);
    }
    
    // Reset the renderer to the initial state
    const replayData = this.player.getReplayData();
    if (replayData) {
      // Reset just the animation controller and clear cards
      this.renderer.resetGameState();
      // Reinitialize with game setup
      await this.renderer.renderGameSetup(replayData);
      // Show first event
      await this.updateDisplay(0);
    }
  }

  private async stepForward(): Promise<void> {
    const stepButton = document.querySelector<HTMLButtonElement>("#btn-step-forward")!;
    
    // Check if replay is currently playing
    const currentState = this.player.getPlaybackState();
    const wasPlaying = currentState.isPlaying;
    
    // If playing, pause it first and wait for current animation to finish
    if (wasPlaying) {
      this.player.pause();
      
      // Wait for any ongoing animation to complete
      while (this.isProcessingEvent) {
        await this.delay(50);
      }
    }
    
    // Don't step if already processing an event (after waiting above)
    if (this.isProcessingEvent) {
      return;
    }
    
    // Validate preconditions before setting processing flag
    const replayData = this.player.getReplayData();
    
    if (!replayData) return;
    
    const nextEventIndex = currentState.currentEventIndex + 1;
    
    // Check if we can step forward
    if (nextEventIndex >= replayData.events.length) {
      // Already at the end
      return;
    }
    
    // Validate that the jump will succeed (forward-only jumping)
    if (nextEventIndex <= currentState.currentEventIndex) {
      console.warn(`stepForward: Invalid jump. Current: ${currentState.currentEventIndex}, Next: ${nextEventIndex}`);
      return;
    }
    
    // Disable button during processing
    stepButton.disabled = true;
    
    // Set processing flag to prevent concurrent operations
    this.isProcessingEvent = true;
    
    try {
      // Process the next event silently (without animations)
      const nextEvent = replayData.events[nextEventIndex];
      this.renderer.processEventsSilently([nextEvent], nextEventIndex, replayData);
      
      // Update player state to the next event
      // This is guaranteed to succeed because we validated above
      this.player.jumpToEvent(nextEventIndex);
      
      // Update the event history to show all events up to the current one
      this.updateEventHistory(nextEventIndex);
      
      // Manually update the event counter since we bypassed the normal event callback
      this.updateEventCounter(nextEventIndex, replayData.events.length);
      
      // Small delay to ensure DOM updates are complete
      await this.delay(10);
    } finally {
      // Clear processing flag and re-enable button
      this.isProcessingEvent = false;
      stepButton.disabled = false;
    }
  }

  /**
   * Update the entire event history up to the current event
   */
  private updateEventHistory(currentEventIndex: number): void {
    const historyContent = document.querySelector("#history-content") as HTMLElement;
    if (!historyContent) return;

    const replayData = this.player.getReplayData();
    if (!replayData) return;

    // Clear history
    historyContent.innerHTML = '';

    // Add all events from 0 to currentEventIndex in reverse order (newest at top)
    for (let i = currentEventIndex; i >= 0; i--) {
      const event = replayData.events[i];
      if (event) {
        const eventEntry = document.createElement('div');
        eventEntry.className = 'history-event-entry';
        
        // Create event number div
        const eventNumber = document.createElement('div');
        eventNumber.className = 'history-event-number';
        eventNumber.textContent = `Event ${i + 1}`;
        
        // Create event text div
        const eventText = document.createElement('div');
        eventText.className = 'history-event-text';
        eventText.innerHTML = this.formatEvent(event); // Safe: formatEvent escapes all user input
        
        eventEntry.appendChild(eventNumber);
        eventEntry.appendChild(eventText);
        historyContent.appendChild(eventEntry);
      }
    }

    // Scroll to top to show the latest event
    historyContent.scrollTop = 0;
  }

  /**
   * Format event for display (same as visualRenderer)
   */
  private formatEvent(event: ReplayEvent): string {
    switch (event.type) {
      case "game_setup":
        return `🎮 Game started with ${event.play_order.length} players`;
      
      case "turn_start":
        return `🔄 Turn ${event.turn_number}: ${this.escapeHtml(event.player)}'s turn (${event.cards_in_deck} cards in deck)`;
      
      case "card_play":
        return `🃏 ${this.escapeHtml(event.player)} played ${this.formatCardName(event.card)}`;
      
      case "combo_play":
        const cards = event.cards.map((c: CardType) => this.formatCardName(c)).join(", ");
        return `🎲 ${this.escapeHtml(event.player)} played ${event.combo_type} combo: [${cards}]${event.target ? ` targeting ${this.escapeHtml(event.target)}` : ""}`;
      
      case "nope":
        const nopeTarget = event.target_player ? ` ${this.escapeHtml(event.target_player)}'s` : '';
        const origAction = event.original_action ? ` ${this.formatCardName(event.original_action)}` : '';
        return `🚫 ${this.escapeHtml(event.player)} played NOPE on${nopeTarget}${origAction}`;
      
      case "card_draw":
        return `📥 ${this.escapeHtml(event.player)} drew ${this.formatCardName(event.card)}`;
      
      case "exploding_kitten_draw":
        return `💣 ${this.escapeHtml(event.player)} drew an EXPLODING KITTEN! ${event.had_defuse ? "(has Defuse)" : "(NO DEFUSE!)"}`;
      
      case "defuse":
        return `🛡️ ${this.escapeHtml(event.player)} defused and inserted kitten at position ${event.insert_position}`;
      
      case "player_elimination":
        return `💀 ${this.escapeHtml(event.player)} was eliminated!`;
      
      case "see_future":
        const seenCards = Array.isArray(event.cards_seen) 
          ? event.cards_seen.map((c: CardType) => this.formatCardName(c)).join(", ")
          : `${event.cards_seen} cards`;
        return `🔮 ${this.escapeHtml(event.player)} used See the Future: [${seenCards}]`;
      
      case "shuffle":
        return `🔀 ${this.escapeHtml(event.player)} shuffled the deck`;
      
      case "favor":
        return `🤝 ${this.escapeHtml(event.player)} played Favor on ${this.escapeHtml(event.target)}`;
      
      case "card_steal":
        return `🎯 ${this.escapeHtml(event.thief)} stole a card from ${this.escapeHtml(event.victim)} (${this.escapeHtml(event.context)})`;
      
      case "card_request":
        return `📢 ${this.escapeHtml(event.requester)} requested ${this.formatCardName(event.requested_card)} from ${this.escapeHtml(event.target)}: ${event.success ? "✅ Success" : "❌ Failed"}`;
      
      case "discard_take":
        return `♻️ ${this.escapeHtml(event.player)} took ${this.formatCardName(event.card)} from discard`;
      
      case "game_end":
        return `🏆 Game Over! Winner: ${event.winner ? this.escapeHtml(event.winner) : "None"}`;
      
      default:
        return `Unknown event: ${(event as any).type}`;
    }
  }

  /**
   * Format card name for display
   */
  private formatCardName(card: string): string {
    return card.replace(/_/g, " ");
  }

  /**
   * Escape HTML to prevent XSS
   */
  private escapeHtml(text: string): string {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Handle agent jump to event (hidden feature for automated testing)
   * Processes all intermediate events AND target event silently to maintain state consistency
   * This saves time by skipping all animations including the target event
   */
  private async handleAgentJump(): Promise<void> {
    const agentJumpInput = document.querySelector<HTMLInputElement>("#agent-jump-to-event")!;
    const targetEventIndex = parseInt(agentJumpInput.value, 10);
    
    if (isNaN(targetEventIndex)) return;

    const currentState = this.player.getPlaybackState();
    const replayData = this.player.getReplayData();
    
    if (!replayData) return;

    // Validate forward-only jump
    if (targetEventIndex <= currentState.currentEventIndex) {
      console.warn(`Agent jump: Cannot jump backward. Current: ${currentState.currentEventIndex}, Target: ${targetEventIndex}`);
      return;
    }

    // Validate bounds
    const maxIndex = replayData.events.length - 1;
    if (targetEventIndex > maxIndex) {
      console.warn(`Agent jump: Target ${targetEventIndex} exceeds max ${maxIndex}`);
      return;
    }

    // Pause playback if playing
    if (currentState.isPlaying) {
      this.player.pause();
    }

    // Wait for any ongoing event processing, with a timeout to prevent infinite loop
    const pollIntervalMs = 50;
    let waitedMs = 0;
    while (this.isProcessingEvent) {
      if (waitedMs >= this.MAX_EVENT_PROCESSING_TIMEOUT_MS) {
        throw new Error("Timeout waiting for previous event processing to complete (isProcessingEvent stuck true).");
      }
      await this.delay(pollIntervalMs);
      waitedMs += pollIntervalMs;
    }

    // Set flag to prevent event callback from rendering during jump
    this.isProcessingEvent = true;

    try {
      // Process all events from current+1 to target (inclusive) silently
      // This includes the target event to save time by not animating it
      const startIndex = currentState.currentEventIndex + 1;
      const eventsToProcess = replayData.events.slice(startIndex, targetEventIndex + 1); // slice(start, end) is exclusive of end, so +1 to include targetEventIndex
      
      if (eventsToProcess.length > 0) {
        // Pass the absolute start index to ensure unique card IDs across multiple jumps
        this.renderer.processEventsSilently(eventsToProcess, startIndex, replayData);
      }

      // Now jump to the target event using the player's method
      // The event has already been processed silently, so this just updates the index
      this.player.jumpToEvent(targetEventIndex);
      
      // Update the event history to show all events up to the current one
      this.updateEventHistory(targetEventIndex);
      
      // Manually update the event counter since we prevented the render callback
      this.updateEventCounter(targetEventIndex, replayData.events.length);
    } finally {
      this.isProcessingEvent = false;
    }
  }

  private async updateDisplay(eventIndex: number): Promise<void> {
    // Set processing flag - if already processing, wait for it to complete
    while (this.isProcessingEvent) {
      await this.delay(10);
    }
    
    this.isProcessingEvent = true;
    let shouldUpdateCounter = false;
    
    try {
      const replayData = this.player.getReplayData();
      if (!replayData) return;

      const event = replayData.events[eventIndex];
      if (!event) return;

      // Calculate deck size at this point
      let deckSize = 33; // Default starting size
      const setupEvent = replayData.events.find(e => e.type === "game_setup");
      if (setupEvent && setupEvent.type === "game_setup") {
        deckSize = setupEvent.deck_size;
      }

      // Count draws and adjust deck size
      for (let i = 0; i <= eventIndex; i++) {
        const e = replayData.events[i];
        if (e.type === "card_draw") {
          deckSize--;
        }
      }

      // Calculate the current top card by looking at previous events
      let currentTopCard: CardType | null = null;
      
      // First, check if we're at or past game_setup (reuse setupEvent from above)
      if (setupEvent && setupEvent.type === "game_setup" && setupEvent.top_card) {
        currentTopCard = setupEvent.top_card;
      }
      
      // Then, look through events up to current index to find the most recent top_card update
      for (let i = 0; i <= eventIndex; i++) {
        const e = replayData.events[i];
        // Events that update the top card: card_draw, defuse, shuffle
        if ((e.type === "card_draw" || e.type === "defuse" || e.type === "shuffle") && e.top_card) {
          currentTopCard = e.top_card as CardType;
        }
      }

      // Find the next card to be drawn (look ahead for next card_draw or exploding_kitten_draw event)
      // Stop if we encounter a shuffle event, as the shuffle changes what the top card will be
      let nextCardToDraw: CardType | null = currentTopCard; // Start with current top card
      for (let i = eventIndex + 1; i < replayData.events.length; i++) {
        const e = replayData.events[i];
        if (e.type === "card_draw") {
          nextCardToDraw = e.card as CardType;
          break;
        } else if (e.type === "exploding_kitten_draw") {
          nextCardToDraw = "EXPLODING_KITTEN" as CardType;
          break;
        } else if (e.type === "shuffle") {
          // Stop looking ahead if there's a shuffle - keep the current top card
          // Don't use the shuffle's top_card yet, as the shuffle hasn't happened
          break;
        }
      }

      // Render the event with animation
      await this.renderer.renderEvent(event, deckSize, nextCardToDraw);
      
      // Update the event history to show all events up to the current one
      this.updateEventHistory(eventIndex);
      
      // Only update counter if we successfully rendered
      shouldUpdateCounter = true;
    } catch (error) {
      console.error('[updateDisplay] Error rendering event:', error);
    } finally {
      this.isProcessingEvent = false;
      
      // Update event counter AFTER clearing the processing flag
      // Only update if we successfully processed the event
      if (shouldUpdateCounter) {
        const replayData = this.player.getReplayData();
        if (replayData) {
          this.updateEventCounter(eventIndex, replayData.events.length);
        }
      }
    }
  }

  private updatePlaybackUI(state: any): void {
    const playPauseBtn = document.querySelector("#btn-play-pause")!;
    playPauseBtn.textContent = state.isPlaying ? "⏸️" : "▶️";
    playPauseBtn.setAttribute("title", state.isPlaying ? "Pause" : "Play");
  }

  private updateEventCounter(current: number, total: number): void {
    const counter = document.querySelector("#event-counter")!;
    counter.textContent = `Event: ${current + 1} / ${total}`;
    // Add data attribute for debugging
    counter.setAttribute('data-current-index', String(current));
  }

  private updateSpeedDisplay(speed: number): void {
    const speedDisplay = document.querySelector("#speed-display")!;
    const speedSlider = document.querySelector<HTMLInputElement>("#speed-slider")!;
    const speedInput = document.querySelector<HTMLInputElement>("#speed-input")!;
    
    speedDisplay.textContent = `${speed.toFixed(1)}x`;
    
    // Update slider if speed is within slider range
    if (speed >= 0.5 && speed <= 10) {
      speedSlider.value = speed.toString();
    }
    
    // Update input field
    speedInput.value = speed.toFixed(1);
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// Initialize the app
new ReplayApp();
