/**
 * Visual game renderer with animations
 */

import type { ReplayData, ReplayEvent } from "./types";
import { GameBoard } from "./gameBoard";
import { AnimationController } from "./animationController";
import { CARD_COLORS } from "./cardConfig";

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
      <div class="visual-layout" style="display: flex; gap: 1rem;">
        <!-- Main game area -->
        <div style="flex: 1; display: flex; flex-direction: column; gap: 1rem;">
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
        
        <!-- Color legend sidebar -->
        <div id="color-legend" style="width: 200px; background: #1a1a1a; padding: 1rem; border-radius: 8px; border: 1px solid #333; height: fit-content; position: sticky; top: 1rem;">
          <h3 style="color: #646cff; margin: 0 0 1rem 0; font-size: 1rem;">Card Colors</h3>
          <div id="legend-items" style="display: flex; flex-direction: column; gap: 0.5rem;">
          </div>
        </div>
      </div>
    `;
    
    // Populate legend
    this.populateLegend();
  }

  /**
   * Populate the color legend
   */
  private populateLegend(): void {
    const legendItems = document.querySelector("#legend-items") as HTMLElement;
    if (!legendItems) return;

    const items = Object.entries(CARD_COLORS).map(([cardType, color]) => {
      const displayName = cardType.replace(/_/g, " ");
      return `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <div style="width: 20px; height: 20px; background: ${color}; border: 1px solid #333; border-radius: 3px; flex-shrink: 0;"></div>
          <div style="color: #ccc; font-size: 0.75rem; line-height: 1.2;">${this.escapeHtml(displayName)}</div>
        </div>
      `;
    }).join('');

    legendItems.innerHTML = items;
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

        case "see_future":
          // Show actual cards that were seen
          await this.animationController.animateSeeFuture(event.player, event.cards_seen);
          break;

        case "nope":
          // Show nope chain animation
          await this.animationController.animateNope(event);
          break;

        case "exploding_kitten_draw":
          await this.animationController.animateExplodingKittenDraw(event.player, event.had_defuse);
          break;

        case "defuse":
          await this.animationController.animateDefuse(event.player, event.insert_position);
          break;

        case "discard_take":
          await this.animationController.animateDiscardTake(event.player, event.card);
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
          ? event.cards_seen.map((c) => this.formatCardName(c)).join(", ")
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

  /**
   * Rebuild entire game state from scratch (for reset and timeline jumps)
   */
  async rebuildFromScratch(events: ReplayEvent[]): Promise<void> {
    // Clear game state
    this.animationController.reset();
    
    // Find game setup event
    const setupEvent = events.find((e) => e.type === "game_setup");
    if (setupEvent && setupEvent.type === "game_setup") {
      this.animationController.initializeGame(
        setupEvent.play_order,
        setupEvent.initial_hands
      );
      this.gameBoard.updateDeckCount(setupEvent.deck_size);
    }
    
    // Rebuild state from all events
    await this.rebuildState(events);
  }

  /**
   * Rebuild state from events without animations (for timeline jumps)
   */
  async rebuildState(events: ReplayEvent[]): Promise<void> {
    // Process all events to rebuild the game state
    let currentPlayer: string | null = null;
    
    for (const event of events) {
      this.updateEventDisplay(event);
      
      // Process events without animations to quickly rebuild state
      switch (event.type) {
        case "turn_start":
          this.gameBoard.updateDeckCount(event.cards_in_deck);
          if (currentPlayer) {
            this.gameBoard.highlightPlayer(currentPlayer, false);
          }
          currentPlayer = event.player;
          this.gameBoard.highlightPlayer(event.player, true);
          break;

        case "card_play":
          // Add to discard pile
          this.gameBoard.addToDiscardPile(event.card);
          break;

        case "combo_play":
          // Add all combo cards to discard pile
          for (const card of event.cards) {
            this.gameBoard.addToDiscardPile(card);
          }
          break;

        case "defuse":
          // Defuse card goes to discard
          this.gameBoard.addToDiscardPile("DEFUSE");
          break;

        case "discard_take":
          // Remove from discard pile
          this.gameBoard.removeFromDiscardPile(event.card);
          break;

        case "player_elimination":
          this.gameBoard.eliminatePlayer(event.player);
          break;

        case "game_end":
          if (currentPlayer) {
            this.gameBoard.highlightPlayer(currentPlayer, false);
            currentPlayer = null;
          }
          break;
      }
    }
    
    // Update animation controller's current player
    this.animationController.setCurrentPlayer(currentPlayer);
  }
}
