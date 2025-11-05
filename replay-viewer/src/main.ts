/**
 * Exploding Kittens Replay Viewer
 * Main application entry point
 */

import "./style.css";
import { ReplayPlayer } from "./replayPlayer";
import { VisualRenderer } from "./visualRenderer";
import { formatEvent } from "./eventFormatter";
import type { ReplayData, CardType } from "./types";

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
              <input type="range" id="speed-slider" min="0.5" max="3" step="0.5" value="1" />
              <span id="speed-display">1.0x</span>
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

        <div class="event-history" id="event-history" style="display: none;">
          <h3>📜 Event History</h3>
          <div class="history-list" id="history-list"></div>
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

    // Speed control
    const speedSlider = document.querySelector<HTMLInputElement>("#speed-slider")!;
    speedSlider.addEventListener("input", (e) => {
      const speed = parseFloat((e.target as HTMLInputElement).value);
      this.player.setSpeed(speed);
      document.querySelector("#speed-display")!.textContent = `${speed.toFixed(1)}x`;
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
      this.updateHistory(index);
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
        this.updateHistory(0);
      }

      // Show controls and update UI AFTER initial event is processed
      document.querySelector<HTMLDivElement>("#playback-controls")!.style.display = "flex";
      document.querySelector<HTMLDivElement>("#event-history")!.style.display = "block";
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
      this.updateHistory(0);
    }
  }

  private async stepForward(): Promise<void> {
    const stepButton = document.querySelector<HTMLButtonElement>("#btn-step-forward")!;
    
    // Wait for any ongoing animations to complete
    if (this.isProcessingEvent) {
      return; // Don't step if already processing an event
    }
    
    // Wait for renderer animations to complete
    while (this.renderer.getIsAnimating()) {
      await this.delay(50);
    }
    
    // Disable button during processing
    stepButton.disabled = true;
    try {
      await this.player.stepForward();
      // Small delay to ensure DOM updates are complete
      await this.delay(10);
    } finally {
      // Re-enable button after processing completes
      stepButton.disabled = false;
    }
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
    let targetReached = false;
    let targetIndex = targetEventIndex;

    try {
      // Process all events from current+1 to target (inclusive) silently
      // This includes the target event to save time by not animating it
      const startIndex = currentState.currentEventIndex + 1;
      const eventsToProcess = replayData.events.slice(startIndex, targetEventIndex + 1); // slice(start, end) is exclusive of end, so +1 to include targetEventIndex
      
      if (eventsToProcess.length > 0) {
        // Pass the absolute start index to ensure unique card IDs across multiple jumps
        this.renderer.processEventsSilently(eventsToProcess, startIndex);
      }

      // Now jump to the target event using the player's method
      // The event has already been processed silently, so this just updates the index
      this.player.jumpToEvent(targetEventIndex);
      
      targetReached = true;
    } finally {
      this.isProcessingEvent = false;
      
      // Update UI only if we successfully reached the target event
      if (targetReached) {
        this.updateEventCounter(targetIndex, replayData.events.length);
        this.updateHistory(targetIndex);
      }
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

      // Find the next card to be drawn (look ahead for next card_draw or exploding_kitten_draw event)
      let nextCardToDraw: CardType | null = null;
      for (let i = eventIndex + 1; i < replayData.events.length; i++) {
        const e = replayData.events[i];
        if (e.type === "card_draw") {
          nextCardToDraw = e.card as CardType;
          break;
        } else if (e.type === "exploding_kitten_draw") {
          nextCardToDraw = "EXPLODING_KITTEN" as CardType;
          break;
        }
      }

      // Render the event with animation
      await this.renderer.renderEvent(event, deckSize, nextCardToDraw);
      
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

  private updateHistory(eventIndex: number): void {
    const replayData = this.player.getReplayData();
    if (!replayData) return;

    const historyList = document.querySelector("#history-list");
    if (!historyList) return;

    // Clear existing history
    historyList.innerHTML = "";

    // Get all events up to the current index
    const eventsToShow = replayData.events.slice(0, eventIndex + 1);

    // Render events in reverse order (latest at top)
    for (let i = eventsToShow.length - 1; i >= 0; i--) {
      const event = eventsToShow[i];
      const historyItem = document.createElement("div");
      historyItem.className = "history-item";
      historyItem.innerHTML = formatEvent(event);
      historyList.appendChild(historyItem);
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// Initialize the app
new ReplayApp();
