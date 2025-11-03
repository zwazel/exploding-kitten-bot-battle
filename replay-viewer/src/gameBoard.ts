/**
 * Game board layout and card rendering
 */

import type { CardType } from "./types";
import { CARD_COLORS, DEFAULT_CARD_COLOR } from "./cardConfig";

export interface Position {
  x: number;
  y: number;
  rotation?: number;
  zIndex?: number;
}

export interface CardElement {
  element: HTMLDivElement;
  cardType: CardType;
  position: Position;
}

/**
 * Visual game board manager
 */
export class GameBoard {
  private container: HTMLElement;
  private boardWidth = 1200;
  private boardHeight = 800;
  private cardElements: Map<string, CardElement> = new Map();

  // Board positions
  private deckPosition: Position = { x: 500, y: 350 };
  private discardPosition: Position = { x: 650, y: 350 };
  
  constructor(container: HTMLElement) {
    this.container = container;
    this.initializeBoard();
  }

  /**
   * Initialize the game board layout
   */
  private initializeBoard(): void {
    this.container.innerHTML = `
      <div class="game-board" style="position: relative; width: ${this.boardWidth}px; height: ${this.boardHeight}px; margin: 0 auto; background: #1a1a1a; border-radius: 12px; overflow: visible;">
        <!-- Deck and discard pile area -->
        <div class="center-area" style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);">
          <div id="deck-pile" class="card-pile" style="position: absolute; left: -150px; top: -60px; width: 100px; height: 140px; border: 2px dashed #555; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
            <span style="color: #888; font-size: 14px;">DECK</span>
          </div>
          <div id="discard-pile" class="card-pile" style="position: absolute; left: 0px; top: -60px; width: 100px; height: 140px; border: 2px dashed #555; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
            <span style="color: #888; font-size: 14px;">DISCARD</span>
          </div>
        </div>

        <!-- Player areas (positioned around the table) -->
        <div id="player-areas" style="position: absolute; width: 100%; height: 100%;"></div>
        
        <!-- Cards container for animations -->
        <div id="cards-container" style="position: absolute; width: 100%; height: 100%; pointer-events: auto;"></div>
      </div>
    `;
  }

  /**
   * Get card color based on type
   */
  private getCardColor(cardType: CardType): string {
    return CARD_COLORS[cardType] || DEFAULT_CARD_COLOR;
  }

  /**
   * Create a card element
   */
  createCard(cardType: CardType, position: Position, id?: string): CardElement {
    const cardId = id || `card-${Date.now()}-${Math.random()}`;
    const color = this.getCardColor(cardType);
    const cardName = cardType.replace(/_/g, " ");

    const card = document.createElement("div");
    card.id = cardId;
    card.className = "game-card";
    card.style.cssText = `
      position: absolute;
      left: ${position.x}px;
      top: ${position.y}px;
      width: 80px;
      height: 112px;
      background: ${color};
      border: 2px solid #333;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: bold;
      color: #000;
      text-align: center;
      padding: 4px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      transition: all 0.3s ease, transform 0.2s ease;
      cursor: pointer;
      word-wrap: break-word;
      transform-origin: center center;
      transform: rotate(${position.rotation || 0}deg);
      z-index: ${position.zIndex || 1};
    `;
    card.textContent = cardName;

    // Add hover effects
    card.addEventListener('mouseenter', () => {
      card.style.transform = `rotate(${position.rotation || 0}deg) scale(1.2) translateY(-10px)`;
      card.style.zIndex = '1000';
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = `rotate(${position.rotation || 0}deg) scale(1)`;
      card.style.zIndex = (position.zIndex || 1).toString();
    });

    const container = this.container.querySelector("#cards-container") as HTMLElement;
    container.appendChild(card);

    const cardElement: CardElement = {
      element: card,
      cardType,
      position: { ...position },
    };

    this.cardElements.set(cardId, cardElement);
    return cardElement;
  }

  /**
   * Move a card to a new position with animation
   */
  async moveCard(cardId: string, newPosition: Position, duration = 500): Promise<void> {
    const cardElement = this.cardElements.get(cardId);
    if (!cardElement) return;

    return new Promise((resolve) => {
      cardElement.element.style.transition = `all ${duration}ms ease`;
      cardElement.element.style.left = `${newPosition.x}px`;
      cardElement.element.style.top = `${newPosition.y}px`;
      if (newPosition.rotation !== undefined) {
        cardElement.element.style.transform = `rotate(${newPosition.rotation}deg)`;
      }
      if (newPosition.zIndex !== undefined) {
        cardElement.element.style.zIndex = newPosition.zIndex.toString();
      }
      cardElement.position = { ...newPosition };

      setTimeout(resolve, duration);
    });
  }

  /**
   * Remove a card from the board
   */
  removeCard(cardId: string): void {
    const cardElement = this.cardElements.get(cardId);
    if (cardElement) {
      cardElement.element.remove();
      this.cardElements.delete(cardId);
    }
  }

  /**
   * Setup player areas around the table
   */
  setupPlayers(playerNames: string[]): void {
    const playerAreas = this.container.querySelector("#player-areas") as HTMLElement;
    playerAreas.innerHTML = "";

    const numPlayers = playerNames.length;
    const angleStep = (2 * Math.PI) / numPlayers;
    const radius = 300;
    const centerX = this.boardWidth / 2;
    const centerY = this.boardHeight / 2;

    playerNames.forEach((name, index) => {
      const angle = angleStep * index - Math.PI / 2; // Start from top
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      const playerArea = document.createElement("div");
      playerArea.id = `player-${name}`;
      playerArea.className = "player-area";
      
      playerArea.style.cssText = `
        position: absolute;
        left: ${x - 100}px;
        top: ${y - 100}px;
        width: 200px;
        height: 200px;
        border: 2px solid #44ff44;
        border-radius: 8px;
        background: rgba(0, 255, 0, 0.1);
        padding: 8px;
      `;

      playerArea.innerHTML = `
        <div style="color: #44ff44; font-weight: bold; margin-bottom: 4px; text-align: center;">${this.escapeHtml(name)}</div>
        <div id="hand-${name}" class="player-hand" data-rotation="0" style="position: relative; min-height: 150px;"></div>
      `;

      playerAreas.appendChild(playerArea);
    });
  }

  /**
   * Get player hand area position with fan layout
   */
  getPlayerHandPosition(playerName: string, cardIndex: number, totalCards: number): Position {
    const handArea = this.container.querySelector(`#hand-${playerName}`) as HTMLElement;
    if (!handArea) return { x: 0, y: 0 };

    const rect = handArea.getBoundingClientRect();
    const containerRect = this.container.querySelector(".game-board")!.getBoundingClientRect();
    
    // Get rotation from data attribute
    const baseRotation = parseFloat(handArea.getAttribute('data-rotation') || '0');

    // Fan layout calculations
    const maxSpread = 30; // Maximum angle spread for the fan
    const cardOverlap = 40; // How much cards overlap (smaller = more overlap)
    
    // Calculate angle for this card in the fan
    const fanAngle = totalCards > 1 
      ? (cardIndex - (totalCards - 1) / 2) * (maxSpread / Math.max(totalCards - 1, 1))
      : 0;
    
    const centerX = rect.left - containerRect.left + rect.width / 2;
    const centerY = rect.top - containerRect.top + rect.height / 2;
    
    const x = centerX + cardIndex * cardOverlap - ((totalCards - 1) * cardOverlap) / 2;
    const y = centerY + Math.abs(fanAngle) * 0.5; // Slight arc effect
    
    return {
      x: x - 40, // Center the card (80px width / 2)
      y: y - 20,
      rotation: baseRotation + fanAngle,
      zIndex: cardIndex + 1
    };
  }

  /**
   * Get deck position
   */
  getDeckPosition(): Position {
    return { ...this.deckPosition };
  }

  /**
   * Get discard pile position
   */
  getDiscardPosition(): Position {
    return { ...this.discardPosition };
  }

  /**
   * Update deck card count
   */
  updateDeckCount(count: number): void {
    const deck = this.container.querySelector("#deck-pile") as HTMLElement;
    if (deck) {
      deck.innerHTML = `<span style="color: #888; font-size: 14px;">DECK<br/>${count}</span>`;
    }
  }

  /**
   * Set the last discarded card (visible on discard pile)
   */
  setLastDiscardedCard(cardType: CardType | null): void {
    const discardPile = this.container.querySelector("#discard-pile") as HTMLElement;
    if (!discardPile) return;

    if (cardType) {
      const color = this.getCardColor(cardType);
      const cardName = cardType.replace(/_/g, " ");
      
      discardPile.innerHTML = `
        <div style="
          width: 90px;
          height: 130px;
          background: ${color};
          border: 2px solid #333;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 9px;
          font-weight: bold;
          color: #000;
          text-align: center;
          padding: 4px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        ">${cardName}</div>
      `;
    } else {
      discardPile.innerHTML = `<span style="color: #888; font-size: 14px;">DISCARD</span>`;
    }
  }

  /**
   * Highlight a player (for their turn)
   */
  highlightPlayer(playerName: string, highlight: boolean): void {
    const playerArea = this.container.querySelector(`#player-${playerName}`) as HTMLElement;
    if (playerArea) {
      if (highlight) {
        playerArea.style.borderColor = "#ffff44";
        playerArea.style.background = "rgba(255, 255, 0, 0.2)";
        playerArea.style.boxShadow = "0 0 20px rgba(255, 255, 0, 0.5)";
      } else {
        playerArea.style.borderColor = "#44ff44";
        playerArea.style.background = "rgba(0, 255, 0, 0.1)";
        playerArea.style.boxShadow = "none";
      }
    }
  }

  /**
   * Mark a player as eliminated
   */
  eliminatePlayer(playerName: string): void {
    const playerArea = this.container.querySelector(`#player-${playerName}`) as HTMLElement;
    if (playerArea) {
      playerArea.style.borderColor = "#ff4444";
      playerArea.style.background = "rgba(255, 0, 0, 0.1)";
      playerArea.style.opacity = "0.5";
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
   * Clear all cards
   */
  clearCards(): void {
    this.cardElements.forEach((card) => card.element.remove());
    this.cardElements.clear();
    this.setLastDiscardedCard(null);
  }
}
