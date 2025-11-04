/**
 * Exploding Kittens Replay Viewer
 * Main application entry point
 */

import "./style.css";
import { ReplayPlayer } from "./replayPlayer";
import { VisualRenderer } from "./visualRenderer";
import type { ReplayData } from "./types";

class ReplayApp {
  private player: ReplayPlayer;
  private renderer!: VisualRenderer;
  private fileInput: HTMLInputElement | null = null;
  private isProcessingEvent = false;
  private lastEventIndex = 0; // Track last event index to detect backward movement

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
            <button id="btn-step-back" title="Step Backward">⏮️</button>
            <button id="btn-play-pause" title="Play/Pause">▶️</button>
            <button id="btn-step-forward" title="Step Forward">⏭️</button>
            
            <div class="speed-control">
              <label for="speed-slider">Speed:</label>
              <input type="range" id="speed-slider" min="0.5" max="3" step="0.5" value="1" />
              <span id="speed-display">1.0x</span>
            </div>
            
            <div class="event-progress">
              <span id="event-counter">Event: 0 / 0</span>
              <input type="range" id="event-slider" min="0" max="0" value="0" />
            </div>
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
    document.querySelector("#btn-stop")?.addEventListener("click", () => this.stop());
    document.querySelector("#btn-step-forward")?.addEventListener("click", () => this.stepForward());
    document.querySelector("#btn-step-back")?.addEventListener("click", () => this.stepBackward());

    // Speed control
    const speedSlider = document.querySelector<HTMLInputElement>("#speed-slider")!;
    speedSlider.addEventListener("input", (e) => {
      const speed = parseFloat((e.target as HTMLInputElement).value);
      this.player.setSpeed(speed);
      document.querySelector("#speed-display")!.textContent = `${speed.toFixed(1)}x`;
    });

    // Event slider
    const eventSlider = document.querySelector<HTMLInputElement>("#event-slider")!;
    let sliderTimeout: number | null = null;
    eventSlider.addEventListener("input", (e) => {
      const index = parseInt((e.target as HTMLInputElement).value);
      
      // Debounce slider movements to avoid rebuilding state on every small change
      if (sliderTimeout !== null) {
        clearTimeout(sliderTimeout);
      }
      
      sliderTimeout = window.setTimeout(async () => {
        // Pause playback while jumping
        const wasPlaying = this.player.getPlaybackState().isPlaying;
        if (wasPlaying) {
          this.player.pause();
        }
        
        // Set the index directly without triggering event callbacks
        // This avoids race condition between updateDisplay and rebuildStateFromScratch
        this.player.getPlaybackState().currentEventIndex = index;
        
        // Rebuild state from scratch to avoid long animation sequences
        try {
          await this.rebuildStateFromScratch();
          
          // Resume if was playing
          if (wasPlaying) {
            this.player.play();
          }
        } catch (error) {
          console.error("Error rebuilding state:", error);
        }
        
        sliderTimeout = null;
      }, 100); // Small debounce delay
    });

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

      // Show controls and update UI
      document.querySelector<HTMLDivElement>("#playback-controls")!.style.display = "flex";
      document.querySelector<HTMLSpanElement>("#file-name")!.textContent = file.name;

      // Update event slider max
      const eventSlider = document.querySelector<HTMLInputElement>("#event-slider")!;
      eventSlider.max = (data.events.length - 1).toString();
      
      // Update event counter
      this.updateEventCounter(0, data.events.length);

      // Reset last event index
      this.lastEventIndex = 0;

      // Show first event
      this.player.jumpToEvent(0);
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

  private stop(): void {
    this.player.stop();
    this.lastEventIndex = 0;
    this.rebuildStateFromScratch();
  }

  /**
   * Rebuild the entire state from scratch without animations
   */
  private async rebuildStateFromScratch(): Promise<void> {
    const replayData = this.player.getReplayData();
    if (!replayData) return;

    // Rebuild entire state up to current index
    const currentIndex = this.player.getPlaybackState().currentEventIndex;
    await this.renderer.rebuildFromScratch(replayData.events.slice(0, currentIndex + 1));
    
    // Update UI
    this.updateEventCounter(currentIndex, replayData.events.length);
    const eventSlider = document.querySelector<HTMLInputElement>("#event-slider")!;
    eventSlider.value = currentIndex.toString();
  }

  private async stepForward(): Promise<void> {
    if (this.isProcessingEvent || this.renderer.getIsAnimating()) {
      return; // Don't step if animation is in progress
    }
    this.player.stepForward();
  }

  private async stepBackward(): Promise<void> {
    if (this.isProcessingEvent || this.renderer.getIsAnimating()) {
      return; // Don't step if animation is in progress
    }
    this.player.stepBackward();
  }

  private async updateDisplay(eventIndex: number): Promise<void> {
    if (this.isProcessingEvent) return;
    
    this.isProcessingEvent = true;
    try {
      const replayData = this.player.getReplayData();
      if (!replayData) return;

      const event = replayData.events[eventIndex];
      if (!event) return;

      // If moving backward, rebuild the entire state from scratch
      // to ensure discard pile and all game state is correct
      if (eventIndex < this.lastEventIndex) {
        await this.rebuildStateFromScratch();
        this.lastEventIndex = eventIndex;
        return;
      }

      // Update last event index for next comparison
      this.lastEventIndex = eventIndex;

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

      // Render the event with animation (forward movement)
      await this.renderer.renderEvent(event, deckSize);
      
      // Update event slider
      const eventSlider = document.querySelector<HTMLInputElement>("#event-slider")!;
      eventSlider.value = eventIndex.toString();
      
      // Update event counter
      this.updateEventCounter(eventIndex, replayData.events.length);
    } finally {
      this.isProcessingEvent = false;
    }
  }

  private updatePlaybackUI(state: any): void {
    const playPauseBtn = document.querySelector("#btn-play-pause")!;
    playPauseBtn.textContent = state.isPlaying ? "⏸️" : "▶️";
    playPauseBtn.setAttribute("title", state.isPlaying ? "Pause" : "Play");
  }

  private updateEventCounter(current: number, total: number): void {
    document.querySelector("#event-counter")!.textContent = `Event: ${current + 1} / ${total}`;
  }
}

// Initialize the app
new ReplayApp();
