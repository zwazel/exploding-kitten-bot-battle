/**
 * Visual game renderer with animations
 */

import type { ReplayData, ReplayEvent } from "./types";
import { GameBoard } from "./gameBoard";
import { AnimationController } from "./animationController";

export class VisualRenderer {
  private container: HTMLElement;
  private gameBoard: GameBoard;
  private animationController: AnimationController;
  private isAnimating = false;

  constructor(container: HTMLElement) {
    this.container = container;
    this.setupLayout();
    
    const boardContainer = document.querySelector("#visual-board") as HTMLElement;
    this.gameBoard = new GameBoard(boardContainer);
    this.animationController = new AnimationController(this.gameBoard);
  }

  /**
   * Setup the layout with board and event log
   */
  private setupLayout(): void {
    this.container.innerHTML = `
      <div class="visual-layout" style="display: flex; flex-direction: column; gap: 1rem;">
        <!-- Game info header -->
        <div id="game-info" class="game-info" style="background: #1a1a1a; padding: 1rem; border-radius: 8px; border: 1px solid #333;">
        </div>
        
        <!-- Visual game board -->
        <div id="visual-board" style="min-height: 800px;">
        </div>
        
        <!-- Current event display -->
        <div id="event-display" class="event-display" style="background: #1a1a1a; padding: 1rem; border-radius: 8px; border: 1px solid #333;">
          <h3 style="color: #888; margin: 0 0 0.5rem 0;">Current Event</h3>
          <div id="event-content" class="event-content" style="padding: 1rem; background: #0f0f0f; border-radius: 6px; border-left: 4px solid #646cff;">
            <em style="color: #888;">No event</em>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Render initial game setup
   */
  async renderGameSetup(replayData: ReplayData): Promise<void> {
    const metadata = replayData.metadata;
    const setupEvent = replayData.events.find((e) => e.type === "game_setup");

    // Update game info
    const gameInfo = document.querySelector("#game-info") as HTMLElement;
    const escapedPlayers = metadata.players.map(p => this.escapeHtml(p)).join(", ");
    const escapedTimestamp = this.escapeHtml(new Date(metadata.timestamp).toLocaleString());

    gameInfo.innerHTML = `
      <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
        <div><strong style="color: #646cff;">Players:</strong> <span style="color: #fff;">${escapedPlayers}</span></div>
        <div><strong style="color: #646cff;">Timestamp:</strong> <span style="color: #fff;">${escapedTimestamp}</span></div>
        ${setupEvent && setupEvent.type === "game_setup" ? `
          <div><strong style="color: #646cff;">Deck Size:</strong> <span style="color: #fff;">${setupEvent.deck_size}</span></div>
        ` : ''}
      </div>
    `;

    // Initialize game board with players
    if (setupEvent && setupEvent.type === "game_setup") {
      this.animationController.initializeGame(
        setupEvent.play_order,
        setupEvent.initial_hands
      );
      this.gameBoard.updateDeckCount(setupEvent.deck_size);
    }
  }

  /**
   * Render a single event with animation
   */
  async renderEvent(event: ReplayEvent, deckSize: number): Promise<void> {
    this.isAnimating = true;

    // Update event display
    this.updateEventDisplay(event);

    // Animate based on event type
    try {
      switch (event.type) {
        case "turn_start":
          await this.animationController.animateTurnStart(event.player, deckSize);
          break;

        case "card_draw":
          await this.animationController.animateCardDraw(event.player, event.card);
          break;

        case "card_play":
          await this.animationController.animateCardPlay(event.player, event.card);
          break;

        case "combo_play":
          await this.animationController.animateComboPlay(event.player, event.cards);
          break;

        case "shuffle":
          await this.animationController.animateShuffle();
          break;

        case "player_elimination":
          await this.animationController.animateElimination(event.player);
          break;

        case "game_end":
          this.animationController.clearHighlight();
          break;

        default:
          // For other events, just show them without animation
          await this.delay(300);
          break;
      }
    } finally {
      this.isAnimating = false;
    }
  }

  /**
   * Update event display text
   */
  private updateEventDisplay(event: ReplayEvent): void {
    const eventContent = document.querySelector("#event-content") as HTMLElement;
    if (eventContent) {
      eventContent.innerHTML = this.formatEvent(event);
    }
  }

  /**
   * Format event for display
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
        const cards = event.cards.map((c) => this.formatCardName(c)).join(", ");
        return `🎲 ${this.escapeHtml(event.player)} played ${event.combo_type} combo: [${cards}]${event.target ? ` targeting ${this.escapeHtml(event.target)}` : ""}`;
      
      case "nope":
        return `🚫 ${this.escapeHtml(event.player)} played NOPE on: ${this.escapeHtml(event.action)}`;
      
      case "card_draw":
        return `📥 ${this.escapeHtml(event.player)} drew ${this.formatCardName(event.card)}`;
      
      case "exploding_kitten_draw":
        return `💣 ${this.escapeHtml(event.player)} drew an EXPLODING KITTEN! ${event.had_defuse ? "(has Defuse)" : "(NO DEFUSE!)"}`;
      
      case "defuse":
        return `🛡️ ${this.escapeHtml(event.player)} defused and inserted kitten at position ${event.insert_position}`;
      
      case "player_elimination":
        return `💀 ${this.escapeHtml(event.player)} was eliminated!`;
      
      case "see_future":
        return `🔮 ${this.escapeHtml(event.player)} used See the Future (saw ${event.cards_seen} cards)`;
      
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
   * Check if currently animating
   */
  getIsAnimating(): boolean {
    return this.isAnimating;
  }

  /**
   * Helper delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Reset the renderer
   */
  reset(): void {
    this.animationController.reset();
    this.setupLayout();
  }
}
