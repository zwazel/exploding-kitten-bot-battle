/**
 * UI rendering and game state visualization
 */

import type { ReplayData, ReplayEvent, CardType } from "./types";

export class ReplayRenderer {
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
  }

  /**
   * Escape HTML to prevent XSS
   */
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Render the initial game setup
   */
  renderGameSetup(replayData: ReplayData): void {
    const metadata = replayData.metadata;
    const setupEvent = replayData.events.find((e) => e.type === "game_setup");

    const escapedPlayers = metadata.players.map(p => this.escapeHtml(p)).join(", ");
    const escapedTimestamp = this.escapeHtml(new Date(metadata.timestamp).toLocaleString());

    let html = `
      <div class="game-info">
        <h2>Game Replay</h2>
        <div class="metadata">
          <div><strong>Players:</strong> ${escapedPlayers}</div>
          <div><strong>Timestamp:</strong> ${escapedTimestamp}</div>
        </div>
      </div>
    `;

    if (setupEvent && setupEvent.type === "game_setup") {
      const escapedPlayOrder = setupEvent.play_order.map(p => this.escapeHtml(p)).join(" → ");
      html += `
        <div class="game-setup">
          <h3>Initial Setup</h3>
          <div class="setup-info">
            <div><strong>Deck Size:</strong> ${setupEvent.deck_size}</div>
            <div><strong>Initial Hand Size:</strong> ${setupEvent.initial_hand_size}</div>
            <div><strong>Play Order:</strong> ${escapedPlayOrder}</div>
          </div>
        </div>
      `;
    }

    this.container.innerHTML = html;
  }

  /**
   * Update display based on current event
   */
  updateDisplay(events: ReplayEvent[]): void {
    const currentEvent = events[events.length - 1];
    if (!currentEvent) return;

    // Find game setup event
    const setupEvent = events.find((e) => e.type === "game_setup");
    if (!setupEvent || setupEvent.type !== "game_setup") return;

    // Build current game state from events
    const gameState = this.buildGameState(events, setupEvent.play_order);

    // Render the current state
    this.renderGameState(gameState, currentEvent);
  }

  /**
   * Build current game state from events
   */
  private buildGameState(events: ReplayEvent[], playOrder: string[]) {
    const players = new Map<string, { hand: string[]; alive: boolean; handSize: number }>();

    // Initialize players
    const setupEvent = events.find((e) => e.type === "game_setup");
    if (setupEvent && setupEvent.type === "game_setup") {
      playOrder.forEach((player) => {
        players.set(player, {
          hand: setupEvent.initial_hands[player] || [],
          alive: true,
          handSize: setupEvent.initial_hands[player]?.length || 0,
        });
      });
    }

    // Update state based on events (simplified - we track hand size from events)
    events.forEach((event) => {
      if (event.type === "turn_start") {
        const player = players.get(event.player);
        if (player) {
          player.handSize = event.hand_size;
        }
      } else if (event.type === "player_elimination") {
        const player = players.get(event.player);
        if (player) {
          player.alive = false;
        }
      }
    });

    return { players, playOrder };
  }

  /**
   * Render the game state
   */
  private renderGameState(
    gameState: {
      players: Map<string, { hand: string[]; alive: boolean; handSize: number }>;
      playOrder: string[];
    },
    currentEvent: ReplayEvent
  ): void {
    const eventLog = this.formatEvent(currentEvent);
    
    const playersHtml = gameState.playOrder
      .map((playerName) => {
        const player = gameState.players.get(playerName);
        if (!player) return "";

        const statusClass = player.alive ? "alive" : "eliminated";
        const statusEmoji = player.alive ? "✅" : "💀";
        const escapedName = this.escapeHtml(playerName);

        return `
          <div class="player-card ${statusClass}">
            <div class="player-name">${statusEmoji} ${escapedName}</div>
            <div class="player-hand">Cards: ${player.handSize}</div>
          </div>
        `;
      })
      .join("");

    const gameStateHtml = `
      <div class="current-state">
        <div class="event-display">
          <h3>Current Event</h3>
          <div class="event-content">${eventLog}</div>
        </div>
        <div class="players-display">
          <h3>Players</h3>
          <div class="players-grid">
            ${playersHtml}
          </div>
        </div>
      </div>
    `;

    const existingGameInfo = this.container.querySelector(".game-info");
    const existingGameSetup = this.container.querySelector(".game-setup");

    // Remove old current state
    const existingState = this.container.querySelector(".current-state");
    if (existingState) existingState.remove();

    // Add new state after setup
    if (existingGameSetup) {
      existingGameSetup.insertAdjacentHTML("afterend", gameStateHtml);
    } else if (existingGameInfo) {
      existingGameInfo.insertAdjacentHTML("afterend", gameStateHtml);
    } else {
      this.container.innerHTML = gameStateHtml;
    }
  }

  /**
   * Format an event for display
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
  private formatCardName(card: CardType): string {
    return card.replace(/_/g, " ");
  }

  /**
   * Get placeholder image for a card
   */
  getCardImage(cardType: CardType): string {
    // For now, return a data URI with a colored box and card name
    const colors: Record<string, string> = {
      EXPLODING_KITTEN: "#ff4444",
      DEFUSE: "#44ff44",
      SKIP: "#ffff44",
      SEE_THE_FUTURE: "#4444ff",
      SHUFFLE: "#ff44ff",
      ATTACK: "#ff8844",
      FAVOR: "#ff44ff",
      NOPE: "#888888",
      TACOCAT: "#88ffff",
      CATTERMELON: "#ffaa88",
      HAIRY_POTATO_CAT: "#aa88ff",
      BEARD_CAT: "#88ff88",
      RAINBOW_RALPHING_CAT: "#ffaaff",
    };

    const color = colors[cardType] || "#cccccc";
    const name = cardType.replace(/_/g, " ");

    // Create SVG placeholder
    const svg = `
      <svg width="100" height="140" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="140" fill="${color}" stroke="#333" stroke-width="2" rx="8"/>
        <text x="50" y="70" text-anchor="middle" fill="#000" font-size="10" font-family="Arial">
          ${name}
        </text>
      </svg>
    `;

    return `data:image/svg+xml;base64,${btoa(svg)}`;
  }
}
