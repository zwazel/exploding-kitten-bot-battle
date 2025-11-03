/**
 * Exploding Kittens Replay Viewer
 * Main application entry point
 */

import "./style.css";
import { ReplayPlayer } from "./replayPlayer";
import { ReplayRenderer } from "./renderer";
import type { ReplayData } from "./types";

class ReplayApp {
  private player: ReplayPlayer;
  private renderer!: ReplayRenderer;
  private fileInput: HTMLInputElement | null = null;

  constructor() {
    this.player = new ReplayPlayer();
    this.initializeUI();
    this.renderer = new ReplayRenderer(
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
              <input type="range" id="speed-slider" min="0.1" max="5" step="0.1" value="1" />
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
            <p>Use the playback controls to play, pause, and navigate through the game events.</p>
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
    eventSlider.addEventListener("input", (e) => {
      const index = parseInt((e.target as HTMLInputElement).value);
      this.player.jumpToEvent(index);
    });

    // Player callbacks
    this.player.onEventChange((_event, index) => {
      this.updateDisplay(index);
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
      this.renderer.renderGameSetup(data);

      // Show controls and update UI
      document.querySelector<HTMLDivElement>("#playback-controls")!.style.display = "flex";
      document.querySelector<HTMLSpanElement>("#file-name")!.textContent = file.name;

      // Update event slider max
      const eventSlider = document.querySelector<HTMLInputElement>("#event-slider")!;
      eventSlider.max = (data.events.length - 1).toString();
      
      // Update event counter
      this.updateEventCounter(0, data.events.length);

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
  }

  private stepForward(): void {
    this.player.stepForward();
  }

  private stepBackward(): void {
    this.player.stepBackward();
  }

  private updateDisplay(eventIndex: number): void {
    const events = this.player.getEventsUpToCurrent();
    this.renderer.updateDisplay(events);
    
    // Update event slider
    const eventSlider = document.querySelector<HTMLInputElement>("#event-slider")!;
    eventSlider.value = eventIndex.toString();
    
    // Update event counter
    const replayData = this.player.getReplayData();
    if (replayData) {
      this.updateEventCounter(eventIndex, replayData.events.length);
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
