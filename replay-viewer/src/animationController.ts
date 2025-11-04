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
  private explodingKittenCardId: string | null = null; // Track exploding kitten card for defuse

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
      
      // Create initial cards in hands with fan layout
      hand.forEach((cardType, index) => {
        const position = this.gameBoard.getPlayerHandPosition(playerName, index, hand.length);
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
    const handPos = this.gameBoard.getPlayerHandPosition(playerName, handIndex, handIndex + 1);

    // Create card at deck position
    const cardId = `${playerName}-draw-${Date.now()}`;
    this.gameBoard.createCard(cardType, deckPos, cardId);

    // Animate to player hand
    await this.delay(100);
    await this.gameBoard.moveCard(cardId, handPos, 500);

    // Add to player's hand and reorganize
    playerHand.push(cardId);
    this.playerHands.set(playerName, playerHand);
    
    // Reorganize hand with new card count
    await this.reorganizePlayerHand(playerName);
  }

  /**
   * Animate card play
   */
  async animateCardPlay(playerName: string, cardType: CardType): Promise<void> {
    const playerHand = this.playerHands.get(playerName) || [];
    
    // Find a card of this type in the player's hand (or use the first card)
    const cardId = playerHand.shift();
    if (!cardId) return;

    this.playerHands.set(playerName, playerHand);

    const discardPos = this.gameBoard.getDiscardPosition();
    
    // Animate to discard pile
    await this.gameBoard.moveCard(cardId, { ...discardPos, rotation: 0, zIndex: 10 }, 500);
    await this.delay(200);

    // Update discard pile to show this card
    this.gameBoard.addToDiscardPile(cardType);

    // Remove from board after updating discard pile
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
   * Reorganize cards in a player's hand to fill gaps with fan layout
   */
  private async reorganizePlayerHand(playerName: string): Promise<void> {
    const playerHand = this.playerHands.get(playerName) || [];
    const moves: Promise<void>[] = [];
    const totalCards = playerHand.length;

    playerHand.forEach((cardId, index) => {
      const newPos = this.gameBoard.getPlayerHandPosition(playerName, index, totalCards);
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
        const position = this.gameBoard.getPlayerHandPosition(playerName, index, size);
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
   * Set the current player (for state rebuilding)
   */
  setCurrentPlayer(playerName: string | null): void {
    this.currentPlayer = playerName;
  }

  /**
   * Animate "See the Future" - show 3 cards from deck that the player sees
   * Note: The SEE_THE_FUTURE card itself has already been played to discard via card_play event
   */
  async animateSeeFuture(playerName: string, topCards: CardType[]): Promise<void> {
    // Small delay before revealing
    await this.delay(300);

    // Show cards prominently in center display popup
    await this.gameBoard.showCenterDisplay(topCards, `🔮 ${playerName} sees the future...`);
    await this.delay(2500); // Show for longer to make it clear and visible

    // Fade out center display
    await this.gameBoard.hideCenterDisplay();
    await this.delay(200);
  }

  /**
   * Animate nope card play with showoff effect for chains
   */
  async animateNope(event: any): Promise<void> {
    // Show nope animation with the original action and the noping player
    const originalAction = event.original_action || "an action";
    const targetPlayer = event.target_player || "someone";
    
    await this.gameBoard.showNopeAnimation(
      event.player,
      targetPlayer,
      originalAction
    );
    
    await this.delay(1500);
    await this.gameBoard.hideNopeAnimation();
  }

  /**
   * Animate exploding kitten draw with explosion effect
   */
  async animateExplodingKittenDraw(playerName: string, hadDefuse: boolean): Promise<void> {
    const deckPos = this.gameBoard.getDeckPosition();
    const centerPos = this.gameBoard.getCenterPosition();

    // Create exploding kitten card and track it
    this.explodingKittenCardId = `exploding-kitten-${Date.now()}`;
    this.gameBoard.createCard("EXPLODING_KITTEN", deckPos, this.explodingKittenCardId);

    // Animate to center
    await this.delay(100);
    await this.gameBoard.moveCard(this.explodingKittenCardId, {
      ...centerPos,
      rotation: 0,
      zIndex: 1000
    }, 500);

    // Show explosion effect if no defuse
    if (!hadDefuse) {
      await this.gameBoard.showCenterDisplay(
        ["EXPLODING_KITTEN"],
        `💥 ${playerName} EXPLODED! 💥`,
        true
      );
      await this.delay(2500);
      await this.gameBoard.hideCenterDisplay();
      this.gameBoard.removeCard(this.explodingKittenCardId);
      this.explodingKittenCardId = null;
    } else {
      // Show that they have a defuse
      await this.gameBoard.showCenterDisplay(
        ["EXPLODING_KITTEN"],
        `💣 ${playerName} drew an Exploding Kitten!`
      );
      await this.delay(1500);
      await this.gameBoard.hideCenterDisplay();
      
      // Keep the card for the defuse animation
    }
  }

  /**
   * Animate defuse card play
   */
  async animateDefuse(playerName: string, _insertPosition: number): Promise<void> {
    const playerHand = this.playerHands.get(playerName) || [];
    const centerPos = this.gameBoard.getCenterPosition();

    // Find defuse card in hand (or use first card)
    const defuseCardId = playerHand.shift();
    if (defuseCardId) {
      this.playerHands.set(playerName, playerHand);

      // Animate defuse card to center
      await this.gameBoard.moveCard(defuseCardId, {
        ...centerPos,
        x: centerPos.x - 60,
        rotation: -10,
        zIndex: 1001
      }, 500);
    }

    // Show both cards in center
    await this.gameBoard.showCenterDisplay(
      ["DEFUSE", "EXPLODING_KITTEN"],
      `🛡️ ${playerName} defused the kitten!`
    );
    await this.delay(2000);
    await this.gameBoard.hideCenterDisplay();

    // Remove exploding kitten card (it goes back to deck)
    if (this.explodingKittenCardId) {
      this.gameBoard.removeCard(this.explodingKittenCardId);
      this.explodingKittenCardId = null;
    }

    // Move defuse to discard pile
    if (defuseCardId) {
      const discardPos = this.gameBoard.getDiscardPosition();
      await this.gameBoard.moveCard(defuseCardId, { ...discardPos, rotation: 0, zIndex: 10 }, 500);
      await this.delay(200);
      
      // Add to discard pile
      this.gameBoard.addToDiscardPile("DEFUSE");
      this.gameBoard.removeCard(defuseCardId);
    }

    // Reorganize hand
    await this.reorganizePlayerHand(playerName);
  }

  /**
   * Animate discard pile take (for 5-unique combo)
   */
  async animateDiscardTake(playerName: string, cardType: CardType): Promise<void> {
    const discardPos = this.gameBoard.getDiscardPosition();
    const playerHand = this.playerHands.get(playerName) || [];
    const handIndex = playerHand.length;
    const handPos = this.gameBoard.getPlayerHandPosition(playerName, handIndex, handIndex + 1);

    // Remove from discard pile
    this.gameBoard.removeFromDiscardPile(cardType);

    // Create card at discard position
    const cardId = `${playerName}-discard-take-${Date.now()}`;
    this.gameBoard.createCard(cardType, discardPos, cardId);

    // Animate to player hand
    await this.delay(100);
    await this.gameBoard.moveCard(cardId, handPos, 500);

    // Add to player's hand
    playerHand.push(cardId);
    this.playerHands.set(playerName, playerHand);
    
    // Reorganize hand
    await this.reorganizePlayerHand(playerName);
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
    this.explodingKittenCardId = null;
    this.gameBoard.clearCards();
  }
}
