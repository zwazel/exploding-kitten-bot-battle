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
  private playbackInterval: number | null = null;
  private eventCallbacks: Set<(event: ReplayEvent, index: number) => void> = new Set();
  private stateChangeCallbacks: Set<(state: PlaybackState) => void> = new Set();

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
  onEventChange(callback: (event: ReplayEvent, index: number) => void): void {
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

    this.playbackState.isPlaying = true;
    this.playbackState.isPaused = false;
    this.notifyStateChange();

    const intervalMs = 1000 / this.playbackState.speed;
    this.playbackInterval = window.setInterval(() => {
      this.stepForward();
    }, intervalMs);
  }

  /**
   * Pause the replay
   */
  pause(): void {
    if (!this.playbackState.isPlaying) return;

    this.playbackState.isPlaying = false;
    this.playbackState.isPaused = true;
    this.notifyStateChange();

    if (this.playbackInterval !== null) {
      clearInterval(this.playbackInterval);
      this.playbackInterval = null;
    }
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
   * Step forward one event
   */
  stepForward(): void {
    if (!this.replayData) return;

    if (this.playbackState.currentEventIndex < this.replayData.events.length - 1) {
      this.playbackState.currentEventIndex++;
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

    // If currently playing, restart with new speed
    if (this.playbackState.isPlaying && this.playbackInterval !== null) {
      clearInterval(this.playbackInterval);
      const intervalMs = 1000 / this.playbackState.speed;
      this.playbackInterval = window.setInterval(() => {
        this.stepForward();
      }, intervalMs);
    }
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
  private notifyCurrentEvent(): void {
    const event = this.getCurrentEvent();
    if (event) {
      this.eventCallbacks.forEach((callback) => {
        callback(event, this.playbackState.currentEventIndex);
      });
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
}
