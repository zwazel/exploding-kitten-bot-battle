/**
 * Animation controller for game events
 */

import type { CardType } from "./types";
import { GameBoard } from "./gameBoard";

/**
 * Manages animations for game events
 */
export class AnimationController {
  private gameBoard: GameBoard;
  private playerHands: Map<string, string[]> = new Map(); // player -> card IDs
  private currentPlayer: string | null = null;

  constructor(gameBoard: GameBoard) {
    this.gameBoard = gameBoard;
  }

  /**
   * Initialize game with players
   */
  initializeGame(playerNames: string[], initialHands: Record<string, CardType[]>): void {
    this.gameBoard.setupPlayers(playerNames);
    this.playerHands.clear();

    // Initialize player hands
    playerNames.forEach((playerName) => {
      this.playerHands.set(playerName, []);
      const hand = initialHands[playerName] || [];
      
      // Create initial cards in hands
      hand.forEach((cardType, index) => {
        const position = this.gameBoard.getPlayerHandPosition(playerName, index);
        const cardId = `${playerName}-card-${index}`;
        this.gameBoard.createCard(cardType, position, cardId);
        this.playerHands.get(playerName)!.push(cardId);
      });
    });
  }

  /**
   * Animate turn start
   */
  async animateTurnStart(playerName: string, deckSize: number): Promise<void> {
    // Unhighlight previous player
    if (this.currentPlayer) {
      this.gameBoard.highlightPlayer(this.currentPlayer, false);
    }

    // Highlight current player
    this.currentPlayer = playerName;
    this.gameBoard.highlightPlayer(playerName, true);
    this.gameBoard.updateDeckCount(deckSize);

    await this.delay(300);
  }

  /**
   * Animate card draw
   */
  async animateCardDraw(playerName: string, cardType: CardType): Promise<void> {
    const deckPos = this.gameBoard.getDeckPosition();
    const playerHand = this.playerHands.get(playerName) || [];
    const handIndex = playerHand.length;
    const handPos = this.gameBoard.getPlayerHandPosition(playerName, handIndex);

    // Create card at deck position
    const cardId = `${playerName}-draw-${Date.now()}`;
    this.gameBoard.createCard(cardType, deckPos, cardId);

    // Animate to player hand
    await this.delay(100);
    await this.gameBoard.moveCard(cardId, handPos, 500);

    // Add to player's hand
    playerHand.push(cardId);
    this.playerHands.set(playerName, playerHand);
  }

  /**
   * Animate card play
   */
  async animateCardPlay(playerName: string, _cardType: CardType): Promise<void> {
    const playerHand = this.playerHands.get(playerName) || [];
    
    // Find a card of this type in the player's hand (or use the first card)
    const cardId = playerHand.shift();
    if (!cardId) return;

    this.playerHands.set(playerName, playerHand);

    const discardPos = this.gameBoard.getDiscardPosition();
    
    // Animate to discard pile
    await this.gameBoard.moveCard(cardId, discardPos, 500);
    await this.delay(200);

    // Remove from board after a brief pause
    this.gameBoard.removeCard(cardId);

    // Reorganize remaining cards in hand
    await this.reorganizePlayerHand(playerName);
  }

  /**
   * Animate combo play (multiple cards)
   */
  async animateComboPlay(playerName: string, cards: CardType[]): Promise<void> {
    for (const cardType of cards) {
      await this.animateCardPlay(playerName, cardType);
      await this.delay(200);
    }
  }

  /**
   * Animate player elimination
   */
  async animateElimination(playerName: string): Promise<void> {
    this.gameBoard.eliminatePlayer(playerName);
    
    // Remove all cards from hand
    const playerHand = this.playerHands.get(playerName) || [];
    for (const cardId of playerHand) {
      this.gameBoard.removeCard(cardId);
    }
    this.playerHands.set(playerName, []);

    await this.delay(500);
  }

  /**
   * Animate shuffle
   */
  async animateShuffle(): Promise<void> {
    const deckPile = document.querySelector("#deck-pile") as HTMLElement;
    if (deckPile) {
      // Visual shuffle effect
      deckPile.style.transition = "transform 0.2s ease";
      for (let i = 0; i < 3; i++) {
        deckPile.style.transform = "rotate(10deg) scale(1.1)";
        await this.delay(100);
        deckPile.style.transform = "rotate(-10deg) scale(1.1)";
        await this.delay(100);
      }
      deckPile.style.transform = "rotate(0deg) scale(1)";
    }
    await this.delay(300);
  }

  /**
   * Reorganize cards in a player's hand to fill gaps
   */
  private async reorganizePlayerHand(playerName: string): Promise<void> {
    const playerHand = this.playerHands.get(playerName) || [];
    const moves: Promise<void>[] = [];

    playerHand.forEach((cardId, index) => {
      const newPos = this.gameBoard.getPlayerHandPosition(playerName, index);
      moves.push(this.gameBoard.moveCard(cardId, newPos, 300));
    });

    await Promise.all(moves);
  }

  /**
   * Update hand sizes without animation (for sync)
   */
  updateHandSizes(handSizes: Record<string, number>): void {
    Object.entries(handSizes).forEach(([playerName, size]) => {
      const currentHand = this.playerHands.get(playerName) || [];
      
      // If hand is smaller, remove cards
      while (currentHand.length > size) {
        const cardId = currentHand.pop();
        if (cardId) this.gameBoard.removeCard(cardId);
      }
      
      // If hand is larger, add placeholder cards (shouldn't happen in normal replay)
      while (currentHand.length < size) {
        const index = currentHand.length;
        const position = this.gameBoard.getPlayerHandPosition(playerName, index);
        const cardId = `${playerName}-placeholder-${index}`;
        this.gameBoard.createCard("NOPE", position, cardId); // Use NOPE as placeholder
        currentHand.push(cardId);
      }
      
      this.playerHands.set(playerName, currentHand);
    });
  }

  /**
   * Clear current player highlight
   */
  clearHighlight(): void {
    if (this.currentPlayer) {
      this.gameBoard.highlightPlayer(this.currentPlayer, false);
      this.currentPlayer = null;
    }
  }

  /**
   * Helper delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Reset the game board
   */
  reset(): void {
    this.playerHands.clear();
    this.currentPlayer = null;
    this.gameBoard.clearCards();
  }
}
