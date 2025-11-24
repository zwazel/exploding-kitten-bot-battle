/**
 * Exploding Kittens Replay Viewer
 * Main application entry point
 */

import { ReplayPlayer } from "./replayPlayer";
import { VisualRenderer } from "./visualRenderer";
import type { ReplayData, CardType, ReplayEvent } from "./types";
import type { ReplayParticipantSummary } from "./api/types";

export class ReplayApp {
  private readonly root: HTMLElement;
  private player: ReplayPlayer;
  private renderer!: VisualRenderer;
  private fileInput: HTMLInputElement | null = null;
  private isProcessingEvent = false;
  private readonly MAX_EVENT_PROCESSING_TIMEOUT_MS = 5000;
  private arenaElements: {
    container: HTMLDivElement;
    status: HTMLParagraphElement;
    participants: HTMLUListElement;
    startButton: HTMLButtonElement;
    downloadButton: HTMLButtonElement;
    botSelect: HTMLSelectElement;
  } | null = null;
  private arenaStartHandler: ((botId: number | null) => Promise<void> | void) | null = null;
  private arenaDownloadHandler: (() => Promise<void> | void) | null = null;
  private arenaBotOptions: { id: number; name: string }[] = [];
  private currentArenaBotId: number | null = null;
  private arenaSelectionHandler: ((botId: number | null) => void) | null = null;

  private rootQuery<T extends Element>(selector: string): T {
    const element = this.root.querySelector<T>(selector);
    if (!element) {
      throw new Error(`Element ${selector} not found in replay viewer container.`);
    }
    return element;
  }

  private rootMaybe<T extends Element>(selector: string): T | null {
    return this.root.querySelector<T>(selector);
  }

  constructor(root: HTMLElement) {
    this.root = root;
    this.player = new ReplayPlayer();
    this.initializeUI();
    this.initializeArenaElements();
    this.renderer = new VisualRenderer(
      this.rootQuery<HTMLDivElement>("#game-display")
    );
    this.setupEventListeners();
  }

  private initializeUI(): void {
    this.root.innerHTML = `
      <div class="replay-viewer">
        <section class="viewer-controls">
          <div class="viewer-controls__primary">
            <input type="file" id="file-input" accept=".json" />
            <label for="file-input" class="file-label">📁 Load Replay File</label>
            <span id="file-name" class="file-name"></span>
          </div>

          <div class="playback-controls is-hidden" id="playback-controls">
            <div class="playback-buttons" role="group" aria-label="Replay controls">
              <button id="btn-stop" title="Stop and Reset" aria-label="Stop replay">⏹️</button>
              <button id="btn-play-pause" title="Play/Pause" aria-label="Play or pause replay">▶️</button>
              <button id="btn-step-forward" title="Step Forward" aria-label="Step forward">⏭️</button>
            </div>

            <div class="speed-control">
              <label for="speed-slider">Speed</label>
              <input type="range" id="speed-slider" min="0.5" max="10" step="0.5" value="1" />
              <div class="speed-input-group">
                <input
                  type="number"
                  id="speed-input"
                  min="0.1"
                  max="100"
                  step="0.1"
                  value="1"
                  inputmode="decimal"
                  title="Set custom playback speed"
                />
                <span id="speed-display" aria-live="polite">1.0x</span>
              </div>
            </div>

            <div class="popup-control">
              <label for="manual-popup-dismiss" title="When checked, popups will pause playback and wait for you to dismiss them">
                <input type="checkbox" id="manual-popup-dismiss" checked />
                Manual popup dismiss
              </label>
            </div>

            <div class="event-progress" aria-live="polite">
              <span id="event-counter">Event: 0 / 0</span>
            </div>

            <!-- Hidden jump control for automated testing/agents only -->
            <input type="hidden" id="agent-jump-to-event" data-testid="agent-jump-to-event" value="0" />
          </div>

          <div class="arena-controls" id="arena-controls" hidden>
            <div class="arena-controls__header">
              <h3>Bot battle</h3>
              <p class="arena-controls__description">Run a match against the arena using one of your uploaded bots.</p>
            </div>
            <div class="arena-controls__body">
              <label class="arena-select" for="arena-bot-select">
                <span>Choose a bot</span>
                <select id="arena-bot-select"></select>
              </label>
              <div class="arena-actions">
                <button id="arena-start" class="primary-button">Start match</button>
                <button id="arena-download" class="secondary-button" disabled>Download replay</button>
              </div>
            </div>
            <p id="arena-status" class="arena-status" hidden></p>
            <ul id="arena-participants" class="arena-participants"></ul>
          </div>
        </section>

        <section class="viewer-layout">
          <div class="viewer-main">
            <div id="game-display" class="game-display">
              <div class="welcome-message">
                <h2>Welcome to the replay viewer</h2>
                <p>Load a replay JSON file or run an arena match to see the action unfold.</p>
              </div>
            </div>
          </div>

          <aside class="viewer-sidebar">
            <section id="card-tracker" class="sidebar-card">
              <header class="sidebar-card__header">
                <h3>Cards in deck</h3>
              </header>
              <div id="card-counts" class="card-counts"></div>
            </section>
            <section id="color-legend" class="sidebar-card">
              <header class="sidebar-card__header">
                <h3>Card colors</h3>
              </header>
              <div id="legend-items" class="legend-items"></div>
            </section>
          </aside>
        </section>
      </div>
    `;
  }

  private initializeArenaElements(): void {
    const container = this.rootMaybe<HTMLDivElement>("#arena-controls");
    if (!container) {
      this.arenaElements = null;
      return;
    }
    this.arenaElements = {
      container,
      status: this.rootQuery<HTMLParagraphElement>("#arena-status"),
      participants: this.rootQuery<HTMLUListElement>("#arena-participants"),
      startButton: this.rootQuery<HTMLButtonElement>("#arena-start"),
      downloadButton: this.rootQuery<HTMLButtonElement>("#arena-download"),
      botSelect: this.rootQuery<HTMLSelectElement>("#arena-bot-select"),
    };
    this.resetArenaControls();
  }

  private resetArenaControls(): void {
    if (!this.arenaElements) {
      return;
    }
    const { container, status, participants, downloadButton, startButton, botSelect } = this.arenaElements;
    container.dataset.loading = "false";
    container.hidden = true;
    status.textContent = "";
    status.hidden = true;
    delete status.dataset.variant;
    participants.innerHTML = "";
    const placeholder = document.createElement("li");
    placeholder.textContent = "No match loaded yet.";
    participants.appendChild(placeholder);
    downloadButton.disabled = true;
    startButton.disabled = true;
    botSelect.innerHTML = "";
    botSelect.disabled = true;
    this.currentArenaBotId = null;
    this.arenaBotOptions = [];
  }

  private setupEventListeners(): void {
    // File input
    this.fileInput = this.rootQuery<HTMLInputElement>("#file-input");
    this.fileInput.addEventListener("change", (e) => this.handleFileLoad(e));

    // Playback controls
    this.rootMaybe<HTMLButtonElement>("#btn-play-pause")?.addEventListener("click", () => this.togglePlayPause());
    this.rootMaybe<HTMLButtonElement>("#btn-stop")?.addEventListener("click", async () => await this.stop());
    this.rootMaybe<HTMLButtonElement>("#btn-step-forward")?.addEventListener("click", () => this.stepForward());

    // Speed control
    const speedSlider = this.rootQuery<HTMLInputElement>("#speed-slider");
    speedSlider.addEventListener("input", (e) => {
      const speed = parseFloat((e.target as HTMLInputElement).value);
      this.applySpeedChange(speed);
    });

    const speedInput = this.rootQuery<HTMLInputElement>("#speed-input");
    const commitSpeedInput = () => {
      const rawValue = parseFloat(speedInput.value);
      if (!Number.isFinite(rawValue)) {
        // Reset to the current playback speed if the input is invalid
        this.updateSpeedControls(this.player.getPlaybackState().speed);
        return;
      }
      this.applySpeedChange(rawValue);
    };

    speedInput.addEventListener("change", commitSpeedInput);
    speedInput.addEventListener("blur", commitSpeedInput);
    speedInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        commitSpeedInput();
        (event.target as HTMLInputElement).blur();
      }
    });

    // Hidden agent jump control - only listens to input event (not MutationObserver)
    // MutationObserver won't detect programmatic value property changes, only attribute changes
    // IMPORTANT: When setting the value of this input programmatically (e.g., in tests),
    // you must also dispatch an input event:
    // agentJumpInput.value = "42";
    // agentJumpInput.dispatchEvent(new Event('input', { bubbles: true }));
    // This ensures the application responds to the change as expected.
    const agentJumpInput = this.rootQuery<HTMLInputElement>("#agent-jump-to-event");
    agentJumpInput.addEventListener("input", () => this.handleAgentJump());

    // Player callbacks
    this.player.onEventChange(async (_event, index) => {
      await this.updateDisplay(index);
    });

    this.player.onStateChange((state) => {
      this.updatePlaybackUI(state);
    });

    // Ensure the speed controls reflect the initial state
    this.updateSpeedControls(this.player.getPlaybackState().speed);

    const arenaStartButton = this.rootMaybe<HTMLButtonElement>("#arena-start");
    arenaStartButton?.addEventListener("click", () => {
      if (!this.arenaStartHandler) return;
      void Promise.resolve(this.arenaStartHandler(this.currentArenaBotId));
    });

    const arenaDownloadButton = this.rootMaybe<HTMLButtonElement>("#arena-download");
    arenaDownloadButton?.addEventListener("click", () => {
      if (!this.arenaDownloadHandler) return;
      void Promise.resolve(this.arenaDownloadHandler());
    });

    const arenaBotSelect = this.rootMaybe<HTMLSelectElement>("#arena-bot-select");
    arenaBotSelect?.addEventListener("change", () => {
      const value = arenaBotSelect.value;
      this.currentArenaBotId = value ? Number.parseInt(value, 10) : null;
      if (!Number.isFinite(this.currentArenaBotId as number)) {
        this.currentArenaBotId = null;
      }
      this.updateArenaStartState();
      this.arenaSelectionHandler?.(this.currentArenaBotId);
    });
  }

  public async loadReplayFromData(data: ReplayData, label = "Replay"): Promise<void> {
    this.player.loadReplay(data);
    await this.renderer.renderGameSetup(data);

    this.updateEventCounter(0, data.events.length);

    if (data.events[0]) {
      await this.updateDisplay(0);
    }

    this.rootQuery<HTMLDivElement>("#playback-controls").classList.remove("is-hidden");
    this.rootQuery<HTMLSpanElement>("#file-name").textContent = label;
  }

  public handleVisibilityChange(isVisible: boolean): void {
    if (isVisible) {
      this.renderer.refreshLayout();
      return;
    }
    this.player.pause();
    this.renderer.dismissPopups();
  }

  public showArenaControls(): void {
    if (!this.arenaElements) return;
    this.arenaElements.container.hidden = false;
    this.updateArenaStartState();
  }

  public hideArenaControls(): void {
    this.resetArenaControls();
  }

  public updateArenaBots(options: { id: number; name: string }[], selectedId: number | null): number | null {
    this.arenaBotOptions = options.slice();
    this.currentArenaBotId = selectedId ?? null;

    if (!this.arenaElements) return this.currentArenaBotId;
    const { botSelect } = this.arenaElements;

    botSelect.innerHTML = "";

    if (options.length === 0) {
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "No bots available";
      botSelect.appendChild(placeholder);
      botSelect.disabled = true;
      this.currentArenaBotId = null;
    } else {
      options.forEach((option) => {
        const element = document.createElement("option");
        element.value = String(option.id);
        element.textContent = option.name;
        botSelect.appendChild(element);
      });

      const hasSelected = options.some((option) => option.id === this.currentArenaBotId);
      if (!hasSelected) {
        this.currentArenaBotId = options[0].id;
      }

      botSelect.value = this.currentArenaBotId !== null ? String(this.currentArenaBotId) : "";
      botSelect.disabled = false;
    }

    this.updateArenaStartState();
    this.arenaSelectionHandler?.(this.currentArenaBotId);
    return this.currentArenaBotId;
  }

  public setArenaStatus(
    message: string,
    variant: "info" | "positive" | "negative" = "info"
  ): void {
    if (!this.arenaElements) return;
    const { status } = this.arenaElements;
    status.textContent = message;
    if (!message) {
      status.hidden = true;
      delete status.dataset.variant;
    } else {
      status.hidden = false;
      status.dataset.variant = variant;
    }
  }

  public setArenaParticipants(participants: ReplayParticipantSummary[]): void {
    if (!this.arenaElements) return;
    const list = this.arenaElements.participants;
    list.innerHTML = "";
    if (participants.length === 0) {
      const li = document.createElement("li");
      li.textContent = "No match loaded yet.";
      list.appendChild(li);
      return;
    }
    participants
      .slice()
      .sort((a, b) => a.placement - b.placement)
      .forEach((participant) => {
        const li = document.createElement("li");
        const winner = participant.is_winner ? " 🏆" : "";
        li.textContent = `${participant.placement}. ${participant.bot_label}${winner}`;
        list.appendChild(li);
      });
  }

  public setArenaLoading(loading: boolean): void {
    if (!this.arenaElements) return;
    this.arenaElements.container.dataset.loading = loading ? "true" : "false";
    this.arenaElements.botSelect.disabled = loading || this.arenaBotOptions.length === 0;
    this.updateArenaStartState();
  }

  public enableArenaDownload(enabled: boolean): void {
    if (!this.arenaElements) return;
    this.arenaElements.downloadButton.disabled = !enabled;
  }

  public onArenaStart(handler: ((botId: number | null) => Promise<void> | void) | null): void {
    this.arenaStartHandler = handler;
    this.updateArenaStartState();
  }

  public onArenaDownload(handler: (() => Promise<void> | void) | null): void {
    this.arenaDownloadHandler = handler;
  }

  public onArenaBotSelectionChange(handler: ((botId: number | null) => void) | null): void {
    this.arenaSelectionHandler = handler;
  }

  private isArenaLoading(): boolean {
    if (!this.arenaElements) return false;
    return this.arenaElements.container.dataset.loading === "true";
  }

  private updateArenaStartState(): void {
    if (!this.arenaElements) return;
    const loading = this.isArenaLoading();
    const hasSelection = this.currentArenaBotId !== null;
    this.arenaElements.startButton.disabled = loading || !hasSelection || !this.arenaStartHandler;
  }

  private async handleFileLoad(e: Event): Promise<void> {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data: ReplayData = JSON.parse(text);
      await this.loadReplayFromData(data, file.name);
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
    const stepButton = this.rootQuery<HTMLButtonElement>("#btn-step-forward");
    
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
    const historyContent = this.rootMaybe<HTMLElement>("#history-content");
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
    const agentJumpInput = this.rootQuery<HTMLInputElement>("#agent-jump-to-event");
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
    const playPauseBtn = this.rootMaybe<HTMLButtonElement>("#btn-play-pause");
    if (playPauseBtn) {
      playPauseBtn.textContent = state.isPlaying ? "⏸️" : "▶️";
      playPauseBtn.setAttribute("title", state.isPlaying ? "Pause" : "Play");
    }

    this.updateSpeedControls(state.speed);
  }

  private applySpeedChange(speed: number): void {
    this.player.setSpeed(speed);
    this.renderer.setSpeed(speed);
    const currentSpeed = this.player.getPlaybackState().speed;
    this.updateSpeedControls(currentSpeed);
  }

  private updateSpeedControls(speed: number): void {
    const speedSlider = this.rootMaybe<HTMLInputElement>("#speed-slider");
    const speedInput = this.rootMaybe<HTMLInputElement>("#speed-input");
    const speedDisplay = this.rootMaybe<HTMLSpanElement>("#speed-display");

    if (speedSlider) {
      const sliderMin = parseFloat(speedSlider.min);
      const sliderMax = parseFloat(speedSlider.max);
      const sliderValue = Math.min(sliderMax, Math.max(sliderMin, speed));
      speedSlider.value = sliderValue.toString();
    }

    if (speedInput) {
      const clampedInput = Math.max(parseFloat(speedInput.min), Math.min(parseFloat(speedInput.max), speed));
      speedInput.value = clampedInput.toString();
    }

    if (speedDisplay) {
      const formatted = speed < 1 ? Number(speed.toFixed(2)).toString() : speed.toFixed(1);
      speedDisplay.textContent = `${formatted}x`;
    }
  }

  private updateEventCounter(current: number, total: number): void {
    const counter = this.rootQuery<HTMLSpanElement>("#event-counter");
    counter.textContent = `Event: ${current + 1} / ${total}`;
    // Add data attribute for debugging
    counter.setAttribute('data-current-index', String(current));
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// Instances are created by src/main.ts
