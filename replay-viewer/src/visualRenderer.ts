/**
 * Visual game renderer with animations
 */

import type { ReplayData, ReplayEvent, CardType } from "./types";
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
          <div id="visual-board">
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
      
      // Find the first card to be drawn from the deck
      let firstCardToDraw: CardType | null = null;
      for (let i = 1; i < replayData.events.length; i++) {
        const e = replayData.events[i];
        if (e.type === "card_draw") {
          firstCardToDraw = e.card as CardType;
          break;
        } else if (e.type === "exploding_kitten_draw") {
          firstCardToDraw = "EXPLODING_KITTEN" as CardType;
          break;
        }
      }
      
      this.gameBoard.updateDeckTopCard(firstCardToDraw, setupEvent.deck_size);
    }
  }

  /**
   * Render a single event with animation
   */
  async renderEvent(event: ReplayEvent, deckSize: number, nextCardToDraw: CardType | null = null): Promise<void> {
    this.isAnimating = true;

    // Animate based on event type
    try {
      switch (event.type) {
        case "turn_start":
          await this.animationController.animateTurnStart(event.player, deckSize, event.turns_remaining, nextCardToDraw);
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

        case "card_steal":
          // Show card steal animation
          await this.animationController.animateCardSteal(
            event.thief,
            event.victim,
            event.stolen_card,
            event.context
          );
          break;

        case "card_request":
          // Show card request animation (3-of-a-kind)
          await this.animationController.animateCardRequest(
            event.requester,
            event.target,
            event.requested_card,
            event.success
          );
          break;

        case "favor":
          // Skip favor animation - it will be shown with the card_steal event that follows
          await this.delay(100);
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
   * Process events silently without animations
   * Used for fast-forwarding during jumps
   * @param events - Array of events to process
   * @param startIndex - Absolute index of the first event in the replay (for unique ID generation)
   */
  processEventsSilently(events: ReplayEvent[], startIndex: number = 0): void {
    // Pass absolute event indices to ensure unique card IDs across multiple jumps
    for (let i = 0; i < events.length; i++) {
      this.animationController.processEventSilently(events[i], startIndex + i);
    }
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
   * Reset just the game state without recreating the layout
   */
  resetGameState(): void {
    this.animationController.reset();
  }
}
