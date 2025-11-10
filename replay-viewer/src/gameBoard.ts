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
  private discardPileStack: CardType[] = []; // Track discard pile cards

  // Board positions (centered on the 1200x800 board)
  // Deck and discard piles are in a centered container
  // Deck: left -150px from center (600px), top -60px from center (400px), 100x140px box
  // Discard: left 0px from center, top -60px from center, 100x140px box
  // Position for card top-left corner to center it on the pile (card is 80x112):
  private deckPosition: Position = { x: 460, y: 354 };
  private discardPosition: Position = { x: 610, y: 354 };
  
  constructor(container: HTMLElement) {
    this.container = container;
    this.initializeBoard();
  }

  /**
   * Initialize the game board layout
   */
  private initializeBoard(): void {
    this.container.innerHTML = `
      <div class="game-board-wrapper" style="
        width: 100%; 
        height: 100%;
        display: flex; 
        justify-content: center; 
        align-items: center;
        container-type: size;
      ">
        <div class="game-board" style="
          position: relative; 
          width: 100%;
          height: 100%;
          max-width: ${this.boardWidth}px; 
          max-height: ${this.boardHeight}px;
          aspect-ratio: ${this.boardWidth} / ${this.boardHeight};
          background: #1a1a1a; 
          border-radius: 12px; 
          overflow: visible;
        ">
          <!-- Deck and discard pile area -->
          <div class="center-area" style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div id="deck-pile" class="card-pile" style="position: absolute; left: -12.5%; top: -7.5%; width: 8.33%; height: 17.5%; border: 2px dashed #555; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
              <span style="color: #888; font-size: 0.875rem;">DECK</span>
            </div>
            <div id="discard-pile" class="card-pile" style="position: absolute; left: 0%; top: -7.5%; width: 8.33%; height: 17.5%; border: 2px dashed #555; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
              <span style="color: #888; font-size: 0.875rem;">DISCARD</span>
            </div>
          </div>

          <!-- Player areas (positioned around the table) -->
          <div id="player-areas" style="position: absolute; width: 100%; height: 100%;"></div>
          
          <!-- Cards container for animations -->
          <div id="cards-container" style="position: absolute; width: 100%; height: 100%; pointer-events: auto;"></div>
          
          <!-- Center display for special cards (See Future, Exploding Kitten, etc) -->
          <div id="center-display" style="position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); display: none; z-index: 1000;"></div>
        </div>
      </div>
    `;
    
    // Update board dimensions based on actual rendered size
    this.updateBoardDimensions();
    
    // Re-update dimensions on window resize
    window.addEventListener('resize', () => this.updateBoardDimensions());
  }
  
  /**
   * Update board dimensions based on actual rendered size
   */
  private updateBoardDimensions(): void {
    const board = this.container.querySelector('.game-board') as HTMLElement;
    if (!board) return;
    
    const rect = board.getBoundingClientRect();
    this.boardWidth = rect.width;
    this.boardHeight = rect.height;
    
    // Update deck and discard positions based on new dimensions
    this.deckPosition = { x: this.boardWidth * 0.383, y: this.boardHeight * 0.4425 };
    this.discardPosition = { x: this.boardWidth * 0.508, y: this.boardHeight * 0.4425 };
  }

  /**
   * Get card color based on type
   */
  private getCardColor(cardType: CardType): string {
    return CARD_COLORS[cardType] || DEFAULT_CARD_COLOR;
  }

  /**
   * Calculate text color based on background color luminance
   * Returns white for dark backgrounds, black for light backgrounds
   * Uses simplified relative luminance calculation (ITU-R BT.601)
   */
  private getTextColor(backgroundColor: string): string {
    // Remove # if present
    let hex = backgroundColor.replace('#', '');
    
    // Handle 3-character shorthand (e.g., 'fff' -> 'ffffff')
    if (hex.length === 3) {
      hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    
    // Validate hex format
    if (hex.length !== 6 || !/^[0-9A-Fa-f]{6}$/.test(hex)) {
      // Default to black text for invalid colors
      return '#000';
    }
    
    // Convert hex to RGB
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    
    // Calculate relative luminance using simplified formula
    // This is a common approximation that works well for basic contrast detection
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    // Use white text for dark backgrounds (luminance < 0.5), black for light
    return luminance < 0.5 ? '#fff' : '#000';
  }

  /**
   * Create a card element
   */
  createCard(cardType: CardType, position: Position, id?: string): CardElement {
    const cardId = id || `card-${Date.now()}-${Math.random()}`;
    const color = this.getCardColor(cardType);
    const textColor = this.getTextColor(color);
    const cardName = cardType.replace(/_/g, " ");
    
    // Card dimensions as percentage of board (80/1200 = 6.67%, 112/800 = 14%)
    const cardWidthPercent = 6.67;
    const cardHeightPercent = 14;

    const card = document.createElement("div");
    card.id = cardId;
    card.className = "game-card";
    card.style.cssText = `
      position: absolute;
      left: ${(position.x / this.boardWidth) * 100}%;
      top: ${(position.y / this.boardHeight) * 100}%;
      width: ${cardWidthPercent}%;
      height: ${cardHeightPercent}%;
      background: ${color};
      border: 2px solid #333;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.625rem;
      font-weight: bold;
      color: ${textColor};
      text-align: center;
      padding: 0.33%;
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
      cardElement.element.style.left = `${(newPosition.x / this.boardWidth) * 100}%`;
      cardElement.element.style.top = `${(newPosition.y / this.boardHeight) * 100}%`;
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
   * Get a card element by ID
   */
  getCardElement(cardId: string): CardElement | undefined {
    return this.cardElements.get(cardId);
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
    // Use percentage of board width for radius (25% of width = 300px on 1200px board)
    const radiusPercent = 25;
    const centerX = 50; // 50% = center
    const centerY = 50; // 50% = center
    
    // Player box size as percentage (16.67% of width = 200px on 1200px board)
    const playerBoxSizePercent = 16.67;

    playerNames.forEach((name, index) => {
      const angle = angleStep * index - Math.PI / 2; // Start from top
      const xPercent = centerX + radiusPercent * Math.cos(angle);
      const yPercent = centerY + radiusPercent * Math.sin(angle);

      const playerArea = document.createElement("div");
      playerArea.id = `player-${name}`;
      playerArea.className = "player-area";
      
      playerArea.style.cssText = `
        position: absolute;
        left: ${xPercent - playerBoxSizePercent / 2}%;
        top: ${yPercent - playerBoxSizePercent / 2}%;
        width: ${playerBoxSizePercent}%;
        height: ${playerBoxSizePercent}%;
        border: 2px solid #44ff44;
        border-radius: 8px;
        background: rgba(0, 255, 0, 0.1);
        padding: 0.67%;
      `;

      playerArea.innerHTML = `
        <div style="color: #44ff44; font-weight: bold; margin-bottom: 4px; text-align: center; font-size: 0.875rem;">${this.escapeHtml(name)}</div>
        <div id="turns-${name}" style="color: #ffa500; font-size: 0.75rem; text-align: center; margin-bottom: 4px;">Turns: <span id="turns-count-${name}">-</span></div>
        <div id="cards-${name}" style="color: #4db8ff; font-size: 0.75rem; text-align: center; margin-bottom: 4px;">Cards: <span id="cards-count-${name}">0</span></div>
        <div id="hand-${name}" class="player-hand" data-rotation="0" style="position: relative; flex: 1; min-height: 0;"></div>
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
    const board = this.container.querySelector(".game-board") as HTMLElement;
    if (!board) return { x: 0, y: 0 };
    
    const boardRect = board.getBoundingClientRect();
    
    // Get rotation from data attribute
    const baseRotation = parseFloat(handArea.getAttribute('data-rotation') || '0');

    // Fan layout calculations
    const maxSpread = 30; // Maximum angle spread for the fan
    // Card overlap as percentage of board width (40/1200 = 3.33%)
    const cardOverlapPercent = 3.33;
    const cardOverlap = (this.boardWidth * cardOverlapPercent) / 100;
    
    // Calculate angle for this card in the fan
    const fanAngle = totalCards > 1 
      ? (cardIndex - (totalCards - 1) / 2) * (maxSpread / Math.max(totalCards - 1, 1))
      : 0;
    
    // Calculate center position relative to board (in pixels)
    const centerX = rect.left - boardRect.left + rect.width / 2;
    const centerY = rect.top - boardRect.top + rect.height / 2;
    
    // Calculate card position with fan layout
    const x = centerX + cardIndex * cardOverlap - ((totalCards - 1) * cardOverlap) / 2;
    const y = centerY + Math.abs(fanAngle) * 0.5; // Slight arc effect
    
    // Card dimensions (80/1200 = 6.67% width, 112/800 = 14% height)
    const cardWidth = this.boardWidth * 0.0667;
    const cardHeight = this.boardHeight * 0.14;
    
    return {
      x: x - cardWidth / 2, // Center the card
      y: y - cardHeight / 2,
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
   * Update deck to show the top card (next card to be drawn)
   */
  updateDeckTopCard(topCard: CardType | null, count: number): void {
    const deck = this.container.querySelector("#deck-pile") as HTMLElement;
    if (!deck) return;

    // Ensure count is a safe integer
    const safeCount = Math.max(0, Math.floor(count));

    if (topCard === null || safeCount === 0) {
      // No cards left or unknown top card - show empty deck
      deck.innerHTML = `<span style="color: #888; font-size: 14px;">DECK<br/>${safeCount}</span>`;
      return;
    }

    // Show the top card
    const color = this.getCardColor(topCard);
    const textColor = this.getTextColor(color);
    const cardName = topCard.replace(/_/g, " ");
    
    deck.innerHTML = `
      <div style="
        width: 90px;
        height: 130px;
        background: ${color};
        border: 2px solid #333;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-size: 9px;
        font-weight: bold;
        color: ${textColor};
        text-align: center;
        padding: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        position: relative;
      ">
        <div style="flex: 1; display: flex; align-items: center; justify-content: center;">
          ${this.escapeHtml(cardName)}
        </div>
        <div style="
          position: absolute;
          bottom: 4px;
          right: 4px;
          background: rgba(0,0,0,0.7);
          color: white;
          padding: 2px 4px;
          border-radius: 3px;
          font-size: 8px;
        ">${safeCount}</div>
      </div>
    `;
  }

  /**
   * Add a card to the discard pile stack
   */
  addToDiscardPile(cardType: CardType): void {
    this.discardPileStack.push(cardType);
    this.renderDiscardPile();
  }

  /**
   * Remove a card from the discard pile (for 5-unique combo)
   */
  removeFromDiscardPile(cardType: CardType): void {
    const index = this.discardPileStack.lastIndexOf(cardType);
    if (index !== -1) {
      this.discardPileStack.splice(index, 1);
    }
    this.renderDiscardPile();
  }

  /**
   * Render the discard pile showing the top card and count
   */
  private renderDiscardPile(): void {
    const discardPile = this.container.querySelector("#discard-pile") as HTMLElement;
    if (!discardPile) return;

    if (this.discardPileStack.length === 0) {
      discardPile.innerHTML = `<span style="color: #888; font-size: 14px;">DISCARD</span>`;
      return;
    }

    // Show the top card (last in stack)
    const topCard = this.discardPileStack[this.discardPileStack.length - 1];
    const color = this.getCardColor(topCard);
    const textColor = this.getTextColor(color);
    const cardName = topCard.replace(/_/g, " ");
    
    discardPile.innerHTML = `
      <div style="
        width: 90px;
        height: 130px;
        background: ${color};
        border: 2px solid #333;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-size: 9px;
        font-weight: bold;
        color: ${textColor};
        text-align: center;
        padding: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        position: relative;
      ">
        <div style="flex: 1; display: flex; align-items: center; justify-content: center;">
          ${this.escapeHtml(cardName)}
        </div>
        <div style="
          position: absolute;
          bottom: 4px;
          right: 4px;
          background: rgba(0,0,0,0.7);
          color: white;
          padding: 2px 4px;
          border-radius: 3px;
          font-size: 8px;
        ">${this.discardPileStack.length}</div>
      </div>
    `;
  }

  /**
   * Set the last discarded card (visible on discard pile) - convenience wrapper for addToDiscardPile
   */
  setLastDiscardedCard(cardType: CardType | null): void {
    if (cardType) {
      this.addToDiscardPile(cardType);
    } else {
      this.discardPileStack = [];
      this.renderDiscardPile();
    }
  }

  /**
   * Highlight a player (for their turn)
   */
  highlightPlayer(playerName: string, highlight: boolean): void {
    const playerArea = this.container.querySelector(`#player-${playerName}`) as HTMLElement;
    if (playerArea) {
      // Check if player is already eliminated (don't change their styling)
      const isEliminated = playerArea.style.opacity === "0.5";
      if (isEliminated) return;
      
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
      playerArea.style.background = "rgba(255, 0, 0, 0.2)";
      playerArea.style.opacity = "0.5";
      // Store eliminated state as data attribute
      playerArea.setAttribute("data-eliminated", "true");
    }
  }

  /**
   * Update the turns remaining display for a player
   */
  updatePlayerTurns(playerName: string, turnsRemaining: number): void {
    const turnsCountElement = this.container.querySelector(`#turns-count-${playerName}`) as HTMLElement;
    if (turnsCountElement) {
      turnsCountElement.textContent = turnsRemaining.toString();
    }
  }

  /**
   * Update the cards in hand display for a player
   */
  updatePlayerCards(playerName: string, cardCount: number): void {
    const cardsCountElement = this.container.querySelector(`#cards-count-${playerName}`) as HTMLElement;
    if (cardsCountElement) {
      cardsCountElement.textContent = cardCount.toString();
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
   * Show cards in center display (for See Future, Exploding Kitten, etc)
   */
  async showCenterDisplay(cards: CardType[], title: string, showExplosion = false): Promise<void> {
    const centerDisplay = this.container.querySelector("#center-display") as HTMLElement;
    if (!centerDisplay) return;

    // Create card elements
    const cardElements = cards.map((cardType, index) => {
      const color = this.getCardColor(cardType);
      const textColor = this.getTextColor(color);
      const cardName = cardType.replace(/_/g, " ");
      const offset = (index - (cards.length - 1) / 2) * 110; // Space cards horizontally
      
      return `
        <div class="center-card" style="
          position: absolute;
          left: ${offset}px;
          width: 90px;
          height: 130px;
          background: ${color};
          border: 3px solid #fff;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: bold;
          color: ${textColor};
          text-align: center;
          padding: 4px;
          box-shadow: 0 4px 16px rgba(0,0,0,0.6);
          animation: centerCardAppear 0.3s ease forwards;
          animation-delay: ${index * 0.1}s;
          opacity: 0;
          transform: scale(0.8);
        ">${this.escapeHtml(cardName)}</div>
      `;
    }).join('');

    const explosionHTML = showExplosion ? `
      <div class="explosion" style="
        position: absolute;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(255,100,0,0.8) 0%, rgba(255,0,0,0.4) 50%, transparent 70%);
        border-radius: 50%;
        animation: explode 0.8s ease-out forwards;
        pointer-events: none;
      "></div>
    ` : '';

    centerDisplay.innerHTML = `
      <style>
        @keyframes centerCardAppear {
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        @keyframes explode {
          0% {
            transform: scale(0);
            opacity: 1;
          }
          50% {
            transform: scale(2);
            opacity: 0.8;
          }
          100% {
            transform: scale(4);
            opacity: 0;
          }
        }
      </style>
      <div style="
        position: relative;
        background: rgba(0, 0, 0, 0.9);
        padding: 30px;
        border-radius: 16px;
        border: 3px solid #646cff;
        box-shadow: 0 0 40px rgba(100, 108, 255, 0.5);
      ">
        <h3 style="
          color: #fff;
          text-align: center;
          margin: 0 0 20px 0;
          font-size: 18px;
          text-shadow: 0 0 10px rgba(100, 108, 255, 0.8);
        ">${this.escapeHtml(title)}</h3>
        <div style="position: relative; height: 140px; min-width: ${cards.length * 110}px;">
          ${explosionHTML}
          ${cardElements}
        </div>
      </div>
    `;
    
    centerDisplay.style.display = 'block';
    
    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 300 + cards.length * 100));
  }

  /**
   * Hide center display
   */
  async hideCenterDisplay(): Promise<void> {
    const centerDisplay = this.container.querySelector("#center-display") as HTMLElement;
    if (!centerDisplay) return;

    centerDisplay.style.opacity = '1';
    centerDisplay.style.transition = 'opacity 0.3s ease';
    centerDisplay.style.opacity = '0';
    
    await new Promise(resolve => setTimeout(resolve, 300));
    centerDisplay.style.display = 'none';
    centerDisplay.innerHTML = '';
  }

  /**
   * Get center position for card animations
   */
  getCenterPosition(): Position {
    // Card dimensions (80/1200 = 6.67% width, 112/800 = 14% height)
    const cardWidth = this.boardWidth * 0.0667;
    const cardHeight = this.boardHeight * 0.14;
    
    return {
      x: this.boardWidth / 2 - cardWidth / 2, // Center - half card width
      y: this.boardHeight / 2 - cardHeight / 2  // Center - half card height
    };
  }

  /**
   * Show nope animation with two cards side by side
   */
  async showNopeAnimation(nopingPlayer: string, targetPlayer: string, originalAction: string): Promise<void> {
    const centerDisplay = this.container.querySelector("#center-display") as HTMLElement;
    if (!centerDisplay) return;

    const actionCardName = originalAction.replace(/_/g, " ");
    
    centerDisplay.innerHTML = `
      <style>
        @keyframes slideInLeft {
          from {
            transform: translateX(-100px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes slideInRight {
          from {
            transform: translateX(100px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes bang {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.2);
          }
        }
      </style>
      <div style="
        position: relative;
        background: rgba(0, 0, 0, 0.95);
        padding: 40px;
        border-radius: 20px;
        border: 4px solid #ff4444;
        box-shadow: 0 0 60px rgba(255, 68, 68, 0.8);
        min-width: 500px;
      ">
        <h2 style="
          color: #ff4444;
          text-align: center;
          margin: 0 0 30px 0;
          font-size: 28px;
          text-shadow: 0 0 15px rgba(255, 68, 68, 0.9);
          animation: bang 0.5s ease infinite;
        ">🚫 NOPE! 🚫</h2>
        
        <div style="display: flex; gap: 60px; align-items: center; justify-content: center;">
          <!-- Original Action Card -->
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            animation: slideInLeft 0.4s ease forwards;
          ">
            <div style="
              width: 120px;
              height: 168px;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              border: 3px solid #fff;
              border-radius: 10px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 12px;
              font-weight: bold;
              color: #fff;
              text-align: center;
              padding: 8px;
              box-shadow: 0 8px 20px rgba(0,0,0,0.5);
              position: relative;
            ">
              <div style="position: absolute; top: 5px; right: 5px; font-size: 20px;">❌</div>
              <div>${this.escapeHtml(actionCardName)}</div>
            </div>
            <div style="color: #888; margin-top: 10px; font-size: 14px;">
              ${this.escapeHtml(targetPlayer)}'s action
            </div>
          </div>
          
          <!-- VS Text -->
          <div style="
            font-size: 36px;
            font-weight: bold;
            color: #ff4444;
            text-shadow: 0 0 10px rgba(255, 68, 68, 0.8);
          ">VS</div>
          
          <!-- Nope Card -->
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            animation: slideInRight 0.4s ease forwards;
          ">
            <div style="
              width: 120px;
              height: 168px;
              background: ${this.getCardColor("NOPE")};
              border: 3px solid #fff;
              border-radius: 10px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 18px;
              font-weight: bold;
              color: ${this.getTextColor(this.getCardColor("NOPE"))};
              text-align: center;
              padding: 8px;
              box-shadow: 0 8px 20px rgba(0,0,0,0.5), 0 0 30px rgba(255, 68, 68, 0.6);
            ">NOPE</div>
            <div style="color: #888; margin-top: 10px; font-size: 14px;">
              ${this.escapeHtml(nopingPlayer)}
            </div>
          </div>
        </div>
      </div>
    `;
    
    centerDisplay.style.display = 'block';
    
    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  /**
   * Hide nope animation
   */
  async hideNopeAnimation(): Promise<void> {
    const centerDisplay = this.container.querySelector("#center-display") as HTMLElement;
    if (!centerDisplay) return;

    centerDisplay.style.opacity = '1';
    centerDisplay.style.transition = 'opacity 0.3s ease';
    centerDisplay.style.opacity = '0';
    
    await new Promise(resolve => setTimeout(resolve, 300));
    centerDisplay.style.display = 'none';
    centerDisplay.innerHTML = '';
  }

  /**
   * Clear all cards
   */
  clearCards(): void {
    this.cardElements.forEach((card) => card.element.remove());
    this.cardElements.clear();
    this.discardPileStack = [];
    this.renderDiscardPile();
  }
}
