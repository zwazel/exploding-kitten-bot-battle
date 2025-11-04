/**
 * Replay player that manages playback state and event progression
 */

import type { ReplayData, ReplayEvent, PlaybackState } from "./types";

export class ReplayPlayer {
  private replayData: ReplayData | null = null;
  private playbackState: PlaybackState = {
    currentEventIndex: 0,
    isPlaying: false,
    speed: 1.0, // 1 event per second by default
    isPaused: false,
  };
  private eventCallbacks: Set<(event: ReplayEvent, index: number) => Promise<void>> = new Set();
  private stateChangeCallbacks: Set<(state: PlaybackState) => void> = new Set();
  private isPlaybackLoopRunning: boolean = false;

  /**
   * Load replay data
   */
  loadReplay(data: ReplayData): void {
    this.replayData = data;
    this.playbackState.currentEventIndex = 0;
    this.playbackState.isPlaying = false;
    this.playbackState.isPaused = false;
    this.notifyStateChange();
  }

  /**
   * Get current replay data
   */
  getReplayData(): ReplayData | null {
    return this.replayData;
  }

  /**
   * Get current playback state
   */
  getPlaybackState(): PlaybackState {
    return { ...this.playbackState };
  }

  /**
   * Subscribe to event changes
   */
  onEventChange(callback: (event: ReplayEvent, index: number) => Promise<void>): void {
    this.eventCallbacks.add(callback);
  }

  /**
   * Subscribe to playback state changes
   */
  onStateChange(callback: (state: PlaybackState) => void): void {
    this.stateChangeCallbacks.add(callback);
  }

  /**
   * Start playing the replay
   */
  play(): void {
    if (!this.replayData || this.playbackState.isPlaying) return;
    
    // Prevent multiple concurrent playback loops
    if (this.isPlaybackLoopRunning) return;

    this.playbackState.isPlaying = true;
    this.playbackState.isPaused = false;
    this.notifyStateChange();

    // Start async playback loop
    this.playbackLoop();
  }

  /**
   * Async playback loop that waits for animations
   */
  private async playbackLoop(): Promise<void> {
    this.isPlaybackLoopRunning = true;
    try {
      while (this.playbackState.isPlaying && this.replayData) {
        if (this.playbackState.currentEventIndex < this.replayData.events.length - 1) {
          // Step forward and wait for event processing
          await this.stepForwardAsync();
          
          // Wait based on speed (time between events)
          const delayMs = 1000 / this.playbackState.speed;
          await this.delay(delayMs);
        } else {
          // Reached the end
          this.pause();
          break;
        }
      }
    } finally {
      this.isPlaybackLoopRunning = false;
    }
  }

  /**
   * Step forward one event asynchronously (waits for callbacks)
   */
  private async stepForwardAsync(): Promise<void> {
    if (!this.replayData) return;

    if (this.playbackState.currentEventIndex < this.replayData.events.length - 1) {
      this.playbackState.currentEventIndex++;
      await this.notifyCurrentEvent();
      this.notifyStateChange();
    }
  }

  /**
   * Pause the replay
   */
  pause(): void {
    if (!this.playbackState.isPlaying) return;

    this.playbackState.isPlaying = false;
    this.playbackState.isPaused = true;
    this.notifyStateChange();
  }

  /**
   * Resume from pause
   */
  resume(): void {
    if (!this.playbackState.isPaused) return;
    this.play();
  }

  /**
   * Stop and reset to beginning
   */
  stop(): void {
    this.pause();
    this.playbackState.currentEventIndex = 0;
    this.playbackState.isPaused = false;
    this.notifyStateChange();
    // Don't notify current event here - the UI handler will manually update the display
    // to avoid race conditions with the reset logic that needs to happen first
  }

  /**
   * Step forward one event (synchronous version for manual stepping)
   * Note: This is called from main.ts which already handles waiting for animations
   */
  stepForward(): void {
    if (!this.replayData) return;

    if (this.playbackState.currentEventIndex < this.replayData.events.length - 1) {
      this.playbackState.currentEventIndex++;
      // Fire and forget - main.ts waits for animations before calling this
      this.notifyCurrentEvent();
      this.notifyStateChange();
    } else {
      // Reached the end
      this.pause();
    }
  }



  /**
   * Set playback speed (events per second)
   */
  setSpeed(speed: number): void {
    this.playbackState.speed = Math.max(0.1, Math.min(10, speed));
    this.notifyStateChange();
    // Speed change will be picked up in the next loop iteration
  }

  /**
   * Get current event
   */
  getCurrentEvent(): ReplayEvent | null {
    if (!this.replayData) return null;
    return this.replayData.events[this.playbackState.currentEventIndex] || null;
  }

  /**
   * Get all events up to current index
   */
  getEventsUpToCurrent(): ReplayEvent[] {
    if (!this.replayData) return [];
    return this.replayData.events.slice(0, this.playbackState.currentEventIndex + 1);
  }

  /**
   * Notify all event change callbacks
   */
  private async notifyCurrentEvent(): Promise<void> {
    const event = this.getCurrentEvent();
    if (event) {
      // Wait for all callbacks to complete
      await Promise.all(
        Array.from(this.eventCallbacks).map(callback => 
          callback(event, this.playbackState.currentEventIndex)
        )
      );
    }
  }

  /**
   * Notify all state change callbacks
   */
  private notifyStateChange(): void {
    this.stateChangeCallbacks.forEach((callback) => {
      callback(this.getPlaybackState());
    });
  }

  /**
   * Helper delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
