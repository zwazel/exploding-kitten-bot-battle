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
  private deckCardCounts: Map<CardType, number> = new Map();

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
          
          <!-- Event History -->
          <div id="event-history" class="event-history" style="background: #1a1a1a; padding: 1rem; border-radius: 8px; border: 1px solid #333;">
            <h3 style="color: #888; margin: 0 0 0.5rem 0;">Event History</h3>
            <div id="history-content" class="history-content" style="max-height: 300px; overflow-y: auto; background: #0f0f0f; border-radius: 6px; padding: 0.5rem;">
              <em style="color: #888;">No events yet</em>
            </div>
          </div>
        </div>
        
        <!-- Sidebar -->
        <div style="width: 200px; display: flex; flex-direction: column; gap: 1rem;">
          <!-- Card tracker -->
          <div id="card-tracker" style="background: #1a1a1a; padding: 1rem; border-radius: 8px; border: 1px solid #333;">
            <h3 style="color: #646cff; margin: 0 0 1rem 0; font-size: 1rem;">Cards in Deck</h3>
            <div id="card-counts" style="display: flex; flex-direction: column; gap: 0.25rem;">
            </div>
          </div>
          
          <!-- Color legend -->
          <div id="color-legend" style="background: #1a1a1a; padding: 1rem; border-radius: 8px; border: 1px solid #333; height: fit-content; position: sticky; top: 1rem;">
            <h3 style="color: #646cff; margin: 0 0 1rem 0; font-size: 1rem;">Card Colors</h3>
            <div id="legend-items" style="display: flex; flex-direction: column; gap: 0.5rem;">
            </div>
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
   * Initialize deck card counts from game setup
   */
  private initializeDeckCardCounts(setupEvent: any): void {
    // Default card counts for a standard deck
    const defaultCounts: Record<string, number> = {
      "DEFUSE": 6,
      "SKIP": 4,
      "SEE_THE_FUTURE": 5,
      "SHUFFLE": 4,
      "FAVOR": 4,
      "ATTACK": 4,
      "NOPE": 5,
      "TACOCAT": 4,
      "CATTERMELON": 4,
      "HAIRY_POTATO_CAT": 4,
      "BEARD_CAT": 4,
      "RAINBOW_RALPHING_CAT": 4,
    };

    // Initialize with default counts
    this.deckCardCounts.clear();
    for (const [cardType, count] of Object.entries(defaultCounts)) {
      this.deckCardCounts.set(cardType as CardType, count);
    }

    // Add exploding kittens (num_players - 1)
    const numPlayers = setupEvent.play_order.length;
    this.deckCardCounts.set("EXPLODING_KITTEN" as CardType, numPlayers - 1);

    // Subtract cards that are in initial hands
    for (const playerHand of Object.values(setupEvent.initial_hands)) {
      for (const card of playerHand as CardType[]) {
        const currentCount = this.deckCardCounts.get(card) || 0;
        this.deckCardCounts.set(card, currentCount - 1);
      }
    }

    // Render the initial counts
    this.renderCardCounts();
  }

  /**
   * Update deck card counts based on an event
   */
  private updateDeckCardCounts(event: ReplayEvent): void {
    if (event.type === "card_draw") {
      // Card was drawn from deck
      const currentCount = this.deckCardCounts.get(event.card) || 0;
      this.deckCardCounts.set(event.card, Math.max(0, currentCount - 1));
      this.renderCardCounts();
    } else if (event.type === "exploding_kitten_draw") {
      // Exploding kitten was drawn
      const currentCount = this.deckCardCounts.get("EXPLODING_KITTEN" as CardType) || 0;
      this.deckCardCounts.set("EXPLODING_KITTEN" as CardType, Math.max(0, currentCount - 1));
      this.renderCardCounts();
    } else if (event.type === "defuse") {
      // Exploding kitten was put back into deck
      const currentCount = this.deckCardCounts.get("EXPLODING_KITTEN" as CardType) || 0;
      this.deckCardCounts.set("EXPLODING_KITTEN" as CardType, currentCount + 1);
      this.renderCardCounts();
    }
  }

  /**
   * Render the card counts in the UI
   */
  private renderCardCounts(): void {
    const cardCountsEl = document.querySelector("#card-counts") as HTMLElement;
    if (!cardCountsEl) return;

    // Sort cards by count (descending) then by name
    const sortedCards = Array.from(this.deckCardCounts.entries())
      .filter(([_, count]) => count > 0)
      .sort((a, b) => {
        if (b[1] !== a[1]) return b[1] - a[1];
        return a[0].localeCompare(b[0]);
      });

    if (sortedCards.length === 0) {
      cardCountsEl.innerHTML = '<div style="color: #888; font-size: 0.75rem;">Deck empty</div>';
      return;
    }

    const html = sortedCards.map(([cardType, count]) => {
      const displayName = cardType.replace(/_/g, " ");
      const color = CARD_COLORS[cardType] || "#666";
      return `
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem; flex: 1; min-width: 0;">
            <div style="width: 12px; height: 12px; background: ${color}; border: 1px solid #333; border-radius: 2px; flex-shrink: 0;"></div>
            <div style="color: #ccc; font-size: 0.7rem; line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${this.escapeHtml(displayName)}">${this.escapeHtml(displayName)}</div>
          </div>
          <div style="color: #fff; font-size: 0.75rem; font-weight: bold; flex-shrink: 0;">${count}</div>
        </div>
      `;
    }).join('');

    cardCountsEl.innerHTML = html;
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
      
      // Initialize deck card counts
      this.initializeDeckCardCounts(setupEvent);
      
      // Use the top_card from the setup event if available
      const topCard = setupEvent.top_card || null;
      this.gameBoard.updateDeckTopCard(topCard, setupEvent.deck_size);
    }
  }

  /**
   * Render a single event with animation
   */
  async renderEvent(event: ReplayEvent, deckSize: number, nextCardToDraw: CardType | null = null): Promise<void> {
    this.isAnimating = true;

    // Update deck card counts
    this.updateDeckCardCounts(event);

    // Animate based on event type
    try {
      switch (event.type) {
        case "turn_start":
          await this.animationController.animateTurnStart(event.player, deckSize, event.turns_remaining, nextCardToDraw);
          break;

        case "card_draw":
          // Update deck top card immediately before animation starts
          if (event.top_card) {
            this.gameBoard.updateDeckTopCard(event.top_card, deckSize - 1);
          }
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
          // Update deck top card immediately before animation starts
          if (event.top_card) {
            this.gameBoard.updateDeckTopCard(event.top_card, deckSize);
          }
          await this.animationController.animateDefuse(event.player, event.insert_position);
          break;

        case "discard_take":
          await this.animationController.animateDiscardTake(event.player, event.card);
          break;

        case "shuffle":
          await this.animationController.animateShuffle();
          // Update deck top card immediately after shuffle animation
          if (event.top_card) {
            this.gameBoard.updateDeckTopCard(event.top_card, deckSize);
          }
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
   * @param replayData - Full replay data to calculate initial top card
   */
  processEventsSilently(events: ReplayEvent[], startIndex: number = 0, replayData: ReplayData | null = null): void {
    // Calculate initial top card by looking at events before startIndex
    let currentTopCard: CardType | null = null;
    let deckSize = 33; // Default deck size
    
    if (replayData) {
      // Get top card and deck size from game_setup
      const setupEvent = replayData.events.find(e => e.type === "game_setup");
      if (setupEvent && setupEvent.type === "game_setup") {
        if (setupEvent.top_card) {
          currentTopCard = setupEvent.top_card;
        }
        deckSize = setupEvent.deck_size;
      }
      
      // Then look through events up to startIndex to find the most recent top_card update
      // and calculate deck size
      for (let i = 0; i < startIndex; i++) {
        const e = replayData.events[i];
        if ((e.type === "card_draw" || e.type === "defuse" || e.type === "shuffle") && e.top_card) {
          currentTopCard = e.top_card as CardType;
        }
        if (e.type === "card_draw") {
          deckSize--;
        }
      }
    }
    
    // Pass absolute event indices to ensure unique card IDs across multiple jumps
    // Track the top card through the events
    for (let i = 0; i < events.length; i++) {
      const event = events[i];
      const previousTopCard = currentTopCard;
      currentTopCard = this.animationController.processEventSilently(event, startIndex + i, currentTopCard);
      
      // Update deck size for card draws
      if (event.type === "card_draw") {
        deckSize--;
      }
      
      // If the top card changed (shuffle, defuse, card_draw), update the deck display
      // Check specific event types first to optimize performance
      if (event.type === "shuffle" || event.type === "defuse" || event.type === "card_draw" || currentTopCard !== previousTopCard) {
        this.gameBoard.updateDeckTopCard(currentTopCard, deckSize);
      }
      
      // Update deck card counts to keep the card tracker in sync
      this.updateDeckCardCounts(event);
    }
  }

  /**
   * Helper delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Set playback speed for animations
   */
  setSpeed(speed: number): void {
    this.animationController.setSpeed(speed);
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
    this.deckCardCounts.clear();
    this.renderCardCounts();
  }
}
