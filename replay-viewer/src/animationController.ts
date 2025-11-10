/**
 * Animation controller for game events
 */

import type { CardType, NopeEvent, ReplayEvent } from "./types";
import { GameBoard } from "./gameBoard";
import { SpecialEventAnimator } from "./specialEventAnimator";

/**
 * Manages animations for game events
 */
export class AnimationController {
  private gameBoard: GameBoard;
  private specialAnimator: SpecialEventAnimator;
  private playerHands: Map<string, string[]> = new Map(); // player -> card IDs
  private currentPlayer: string | null = null;
  private explodingKittenCardId: string | null = null; // Track exploding kitten card for defuse
  private playOrder: string[] = []; // Track turn order for attack animations
  private speedMultiplier: number = 1.0;

  constructor(gameBoard: GameBoard) {
    this.gameBoard = gameBoard;
    this.specialAnimator = new SpecialEventAnimator(document.body);
  }

  /**
   * Set the speed multiplier for animations
   */
  setSpeed(speed: number): void {
    this.speedMultiplier = speed;
    this.specialAnimator.setSpeed(speed);
  }

  /**
   * Initialize game with players
   */
  initializeGame(playerNames: string[], initialHands: Record<string, CardType[]>): void {
    this.gameBoard.setupPlayers(playerNames);
    this.playerHands.clear();
    this.playOrder = [...playerNames]; // Store play order

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
      
      // Update initial cards counter
      this.gameBoard.updatePlayerCards(playerName, hand.length);
    });
  }

  /**
   * Animate turn start
   */
  async animateTurnStart(playerName: string, deckSize: number, turnsRemaining: number, nextCardToDraw: CardType | null = null): Promise<void> {
    // Unhighlight previous player and reset their turn counter
    if (this.currentPlayer) {
      this.gameBoard.highlightPlayer(this.currentPlayer, false);
      this.gameBoard.updatePlayerTurns(this.currentPlayer, 0);
    }

    // Highlight current player
    this.currentPlayer = playerName;
    this.gameBoard.highlightPlayer(playerName, true);
    this.gameBoard.updateDeckTopCard(nextCardToDraw, deckSize);
    this.gameBoard.updatePlayerTurns(playerName, turnsRemaining);
    
    // Update cards in hand for current player
    const playerHand = this.playerHands.get(playerName) || [];
    this.gameBoard.updatePlayerCards(playerName, playerHand.length);

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
    
    // Update cards counter
    this.gameBoard.updatePlayerCards(playerName, playerHand.length);
    
    // Reorganize hand with new card count
    await this.reorganizePlayerHand(playerName);
  }

  /**
   * Animate card play
   */
  async animateCardPlay(playerName: string, cardType: CardType): Promise<void> {
    const playerHand = this.playerHands.get(playerName) || [];
    
    // Find a card of this type in the player's hand by matching the card type
    const cardIndex = this.findCardIndexByType(playerHand, cardType);
    let cardId: string | undefined;
    
    if (cardIndex === -1) {
      console.warn(`Card type ${cardType} not found in ${playerName}'s hand, using first card as fallback`);
      // Fallback: use first card if exact match not found
      if (playerHand.length === 0) return;
      cardId = playerHand.shift();
    } else {
      // Remove the specific card from the hand
      cardId = playerHand[cardIndex];
      playerHand.splice(cardIndex, 1);
    }
    
    if (!cardId) return;

    this.playerHands.set(playerName, playerHand);
    
    // Update cards counter
    this.gameBoard.updatePlayerCards(playerName, playerHand.length);

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

    // Special handling for ATTACK cards - show who gets attacked
    if (cardType === "ATTACK") {
      const nextPlayer = this.getNextPlayer(playerName);
      if (nextPlayer) {
        await this.animateAttack(playerName, nextPlayer);
      }
    }
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
    
    // Update cards counter
    this.gameBoard.updatePlayerCards(playerName, 0);

    await this.delay(500);
  }

  /**
   * Animate shuffle
   */
  async animateShuffle(): Promise<void> {
    const deckPile = document.querySelector("#deck-pile") as HTMLElement;
    if (deckPile) {
      // Use unified simple animation
      await this.specialAnimator.showSimple({
        element: deckPile,
        type: "shake",
        duration: 600
      });
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

    // Use unified showcase animation
    await this.specialAnimator.showShowcase({
      cards: topCards,
      title: `🔮 ${playerName} sees the future...`,
      subtitle: `Top ${topCards.length} cards of the deck`,
      duration: 2500
    });
  }

  /**
   * Animate nope card play with showoff effect for chains
   */
  async animateNope(event: NopeEvent): Promise<void> {
    const playerName = event.player;
    const playerHand = this.playerHands.get(playerName) || [];
    
    // Find the NOPE card in the player's hand
    const nopeCardIndex = this.findCardIndexByType(playerHand, "NOPE");
    let nopeCardId: string | undefined;
    
    if (nopeCardIndex === -1) {
      if (playerHand.length === 0) {
        console.warn(`NOPE card not found and hand is empty for ${playerName}, skipping NOPE animation`);
        return;
      }
      console.warn(`NOPE card not found in ${playerName}'s hand, using first card as fallback`);
      // Fallback: use first card if nope not found
      nopeCardId = playerHand.shift();
    } else {
      // Remove the nope card from the hand
      nopeCardId = playerHand[nopeCardIndex];
      playerHand.splice(nopeCardIndex, 1);
    }
    
    if (nopeCardId) {
      this.playerHands.set(playerName, playerHand);
      
      // Update cards counter
      this.gameBoard.updatePlayerCards(playerName, playerHand.length);
      
      // Animate nope card to discard pile
      const discardPos = this.gameBoard.getDiscardPosition();
      await this.gameBoard.moveCard(nopeCardId, { ...discardPos, rotation: 0, zIndex: 10 }, 500);
      await this.delay(200);
    }
    
    // Show nope animation using unified target system
    const originalAction = event.original_action || "an action";
    const targetPlayer = event.target_player || "someone";
    
    await this.specialAnimator.showTarget({
      sourcePlayer: playerName,
      targetPlayer: targetPlayer,
      action: `🚫 ${playerName} NOPES ${targetPlayer}'s ${originalAction}!`,
      icon: "🚫",
      duration: 1800
    });
    
    // Add nope card to discard pile and remove from board
    if (nopeCardId) {
      this.gameBoard.addToDiscardPile("NOPE");
      this.gameBoard.removeCard(nopeCardId);
    }
    
    // Reorganize remaining cards in hand
    await this.reorganizePlayerHand(playerName);
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

    // Show explosion effect if no defuse using unified showcase
    if (!hadDefuse) {
      await this.specialAnimator.showShowcase({
        cards: ["EXPLODING_KITTEN"],
        title: `💥 ${playerName} EXPLODED! 💥`,
        showExplosion: true,
        duration: 2500
      });
      this.gameBoard.removeCard(this.explodingKittenCardId);
      this.explodingKittenCardId = null;
    }
    // If has defuse, wait for the defuse animation to show both cards together
  }

  /**
   * Animate defuse card play - shows both exploding kitten and defuse together
   */
  async animateDefuse(playerName: string, _insertPosition: number): Promise<void> {
    const playerHand = this.playerHands.get(playerName) || [];
    const centerPos = this.gameBoard.getCenterPosition();

    // Find defuse card in hand by matching card type
    const defuseCardIndex = this.findCardIndexByType(playerHand, "DEFUSE");
    let defuseCardId: string | undefined;
    
    if (defuseCardIndex === -1) {
      console.warn(`DEFUSE card not found in ${playerName}'s hand, using first card as fallback`);
      // Fallback: use first card if defuse not found
      defuseCardId = playerHand.shift();
    } else {
      // Remove the defuse card from the hand
      defuseCardId = playerHand[defuseCardIndex];
      playerHand.splice(defuseCardIndex, 1);
    }
    
    if (defuseCardId) {
      this.playerHands.set(playerName, playerHand);
      
      // Update cards counter
      this.gameBoard.updatePlayerCards(playerName, playerHand.length);

      // Animate defuse card to center
      await this.gameBoard.moveCard(defuseCardId, {
        ...centerPos,
        x: centerPos.x - 60,
        rotation: -10,
        zIndex: 1001
      }, 500);
    }

    // Show both cards together in one popup
    await this.specialAnimator.showShowcase({
      cards: ["EXPLODING_KITTEN", "DEFUSE"],
      title: `🛡️ ${playerName} defused the kitten!`,
      subtitle: "The Exploding Kitten is returned to the deck",
      duration: 2000
    });

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
    
    // Update cards counter
    this.gameBoard.updatePlayerCards(playerName, playerHand.length);
    
    // Reorganize hand
    await this.reorganizePlayerHand(playerName);
  }

  /**
   * Animate card steal (2-of-a-kind or favor)
   * For favor, this shows both the request and the card being given in one animation
   */
  async animateCardSteal(thief: string, victim: string, stolenCard?: CardType, context?: string): Promise<void> {
    // Find and remove the stolen card from victim's hand
    const victimHand = this.playerHands.get(victim) || [];
    let stolenCardId: string | undefined;
    
    if (victimHand.length > 0) {
      // If the replay specifies which card was stolen, find and remove that card
      if (stolenCard) {
        // Find a card of the stolen type in victim's hand
        const cardIndex = this.findCardIndexByType(victimHand, stolenCard);
        if (cardIndex !== -1) {
          stolenCardId = victimHand.splice(cardIndex, 1)[0];
        }
      }
      
      // Fallback: if no specific card was found, take the first card
      if (!stolenCardId && victimHand.length > 0) {
        stolenCardId = victimHand.shift();
      }
    }
    
    // Show transfer animation using unified system
    if (context === "favor") {
      // For favor, show both the request and the card given in one popup
      await this.specialAnimator.showTransfer({
        fromPlayer: victim,
        toPlayer: thief,
        card: stolenCard,
        title: `🤝 ${thief} asks ${victim} for a Favor`,
        subtitle: stolenCard ? `${victim} gives ${this.formatCardName(stolenCard)}` : "Card given",
        duration: 2500
      });
    } else {
      // For steals (2-of-a-kind), show normal steal animation
      await this.specialAnimator.showTransfer({
        fromPlayer: victim,
        toPlayer: thief,
        card: stolenCard,
        title: `🎯 ${thief} steals from ${victim}!`,
        subtitle: context || "Card stolen",
        duration: 2000
      });
    }
    
    // Now animate the actual card movement from victim to thief
    if (stolenCardId) {
      // Get thief's hand and calculate new position
      const thiefHand = this.playerHands.get(thief) || [];
      const handIndex = thiefHand.length;
      const thiefHandPos = this.gameBoard.getPlayerHandPosition(thief, handIndex, handIndex + 1);
      
      // Animate card to thief's hand
      await this.gameBoard.moveCard(stolenCardId, thiefHandPos, 500);
      
      // Update victim's hand state only after the card has been animated away
      this.playerHands.set(victim, victimHand);
      
      // Add to thief's hand
      thiefHand.push(stolenCardId);
      this.playerHands.set(thief, thiefHand);
      
      // Reorganize both hands to fill gaps
      await Promise.all([
        this.reorganizePlayerHand(victim),
        this.reorganizePlayerHand(thief)
      ]);
    }
  }

  /**
   * Animate card request (3-of-a-kind)
   */
  async animateCardRequest(requester: string, target: string, requestedCard: CardType, success: boolean): Promise<void> {
    let requestedCardId: string | undefined;
    
    if (success) {
      // Find and remove the requested card from target's hand
      const targetHand = this.playerHands.get(target) || [];
      const cardIndex = this.findCardIndexByType(targetHand, requestedCard);
      
      if (cardIndex !== -1) {
        requestedCardId = targetHand.splice(cardIndex, 1)[0];
      }
      
      // Show successful transfer animation
      await this.specialAnimator.showTransfer({
        fromPlayer: target,
        toPlayer: requester,
        card: requestedCard,
        title: `📢 ${requester} requests ${this.formatCardName(requestedCard)}`,
        subtitle: `✅ ${target} has it and must give it`,
        duration: 2000
      });
      
      // Now animate the actual card movement from target to requester
      if (requestedCardId) {
        // Get requester's hand and calculate new position
        const requesterHand = this.playerHands.get(requester) || [];
        const handIndex = requesterHand.length;
        const requesterHandPos = this.gameBoard.getPlayerHandPosition(requester, handIndex, handIndex + 1);
        
        // Animate card to requester's hand
        await this.gameBoard.moveCard(requestedCardId, requesterHandPos, 500);
        
        // Update target's hand state only after the card has been animated away
        this.playerHands.set(target, targetHand);
        
        // Add to requester's hand
        requesterHand.push(requestedCardId);
        this.playerHands.set(requester, requesterHand);
        
        // Reorganize both hands to fill gaps
        await Promise.all([
          this.reorganizePlayerHand(target),
          this.reorganizePlayerHand(requester)
        ]);
      }
    } else {
      // Show failed request
      await this.specialAnimator.showTarget({
        sourcePlayer: requester,
        targetPlayer: target,
        action: `📢 ${requester} requests ${this.formatCardName(requestedCard)}`,
        icon: "❌",
        duration: 1500
      });
    }
  }

  /**
   * Animate favor (choosing a card to give)
   */
  async animateFavor(player: string, target: string): Promise<void> {
    // Show target animation to indicate favor being played
    await this.specialAnimator.showTarget({
      sourcePlayer: player,
      targetPlayer: target,
      action: `🤝 ${player} asks ${target} for a Favor`,
      icon: "🤝",
      duration: 1500
    });
  }

  /**
   * Animate attack (next player takes 2 turns)
   */
  async animateAttack(attacker: string, target: string): Promise<void> {
    // Show attack animation using unified target system
    await this.specialAnimator.showTarget({
      sourcePlayer: attacker,
      targetPlayer: target,
      action: `⚔️ ${attacker} attacks ${target}!`,
      icon: "⚔️",
      duration: 1800
    });
  }

  /**
   * Format card name for display
   */
  private formatCardName(cardType: CardType | string): string {
    return cardType.replace(/_/g, " ");
  }

  /**
   * Get the next player in turn order (for ATTACK animation)
   * Returns the next alive player after the given player
   */
  private getNextPlayer(currentPlayerName: string): string | null {
    if (this.playOrder.length === 0) return null;

    const currentIndex = this.playOrder.indexOf(currentPlayerName);
    if (currentIndex === -1) return null;

    // Find next alive player in circular turn order
    for (let i = 1; i < this.playOrder.length; i++) {
      const nextIndex = (currentIndex + i) % this.playOrder.length;
      const nextPlayer = this.playOrder[nextIndex];
      
      // Check if player is still alive (has a hand with cards or is in playerHands)
      if (this.playerHands.has(nextPlayer)) {
        return nextPlayer;
      }
    }

    return null;
  }

  /**
   * Find the index of a card in the player's hand by matching card type
   * Uses the gameBoard's cardElements map to check the actual card type
   */
  private findCardIndexByType(playerHand: string[], targetCardType: CardType): number {
    for (let i = 0; i < playerHand.length; i++) {
      const cardId = playerHand[i];
      const cardElement = this.gameBoard.getCardElement(cardId);
      if (cardElement && cardElement.cardType === targetCardType) {
        return i;
      }
    }
    return -1; // Not found
  }

  /**
   * Helper delay function with speed scaling
   */
  private delay(ms: number): Promise<void> {
    const scaledMs = ms / this.speedMultiplier;
    return new Promise((resolve) => setTimeout(resolve, scaledMs));
  }

  /**
   * Reset the game board
   */
  reset(): void {
    this.playerHands.clear();
    this.currentPlayer = null;
    this.explodingKittenCardId = null;
    this.gameBoard.clearCards();
    // Cleanup special animator resources
    this.specialAnimator.destroy();
    // Recreate animator for reuse
    this.specialAnimator = new SpecialEventAnimator(document.body);
  }

  /**
   * Process event state updates without animations
   * Used for fast-forwarding through events during jump
   * @param event - The event to process
   * @param eventIndex - Optional index to help generate unique card IDs when processing batches
   * @param currentTopCard - The current top card of the deck (tracked across events)
   */
  processEventSilently(event: ReplayEvent, eventIndex: number = 0, currentTopCard: CardType | null = null): CardType | null {
    switch (event.type) {
      case "turn_start":
        // Update current player state
        if (this.currentPlayer) {
          this.gameBoard.highlightPlayer(this.currentPlayer, false);
          this.gameBoard.updatePlayerTurns(this.currentPlayer, 0);
        }
        this.currentPlayer = event.player;
        this.gameBoard.highlightPlayer(event.player, true);
        // Use the tracked top card instead of null to maintain consistency during shuffle events
        // This ensures the deck shows the correct top card when stepping through events
        this.gameBoard.updateDeckTopCard(currentTopCard, event.cards_in_deck);
        this.gameBoard.updatePlayerTurns(event.player, event.turns_remaining);
        
        // Update cards in hand for current player
        const currentPlayerHand = this.playerHands.get(event.player) || [];
        this.gameBoard.updatePlayerCards(event.player, currentPlayerHand.length);
        break;

      case "card_draw":
        // Add card to player's hand state
        const playerHand = this.playerHands.get(event.player) || [];
        const cardId = `${event.player}-draw-${eventIndex}-${playerHand.length}`;
        const handPos = this.gameBoard.getPlayerHandPosition(event.player, playerHand.length, playerHand.length + 1);
        this.gameBoard.createCard(event.card, handPos, cardId);
        playerHand.push(cardId);
        this.playerHands.set(event.player, playerHand);
        this.gameBoard.updatePlayerCards(event.player, playerHand.length);
        // Update top card from the event
        if (event.top_card) {
          currentTopCard = event.top_card as CardType;
        }
        break;

      case "card_play":
        // Remove card from player's hand state
        this.removeCardFromHand(event.player, event.card);
        this.gameBoard.addToDiscardPile(event.card);
        const playHand = this.playerHands.get(event.player) || [];
        this.gameBoard.updatePlayerCards(event.player, playHand.length);
        break;

      case "combo_play":
        // Remove multiple cards from player's hand
        if (event.cards) {
          event.cards.forEach((cardType: CardType) => {
            this.removeCardFromHand(event.player, cardType);
            this.gameBoard.addToDiscardPile(cardType);
          });
          const comboHand = this.playerHands.get(event.player) || [];
          this.gameBoard.updatePlayerCards(event.player, comboHand.length);
        }
        break;

      case "player_elimination":
        // Mark player as eliminated
        this.gameBoard.eliminatePlayer(event.player);
        const eliminatedHand = this.playerHands.get(event.player) || [];
        eliminatedHand.forEach(id => this.gameBoard.removeCard(id));
        this.playerHands.set(event.player, []);
        this.gameBoard.updatePlayerCards(event.player, 0);
        break;

      case "exploding_kitten_draw":
        // Track exploding kitten if player has defuse
        if (event.had_defuse) {
          const hand = this.playerHands.get(event.player) || [];
          const ektCardId = `${event.player}-ekt-${eventIndex}-${hand.length}`;
          const handPos = this.gameBoard.getPlayerHandPosition(event.player, hand.length, hand.length + 1);
          this.gameBoard.createCard("EXPLODING_KITTEN", handPos, ektCardId);
          hand.push(ektCardId);
          this.playerHands.set(event.player, hand);
          this.gameBoard.updatePlayerCards(event.player, hand.length);
          this.explodingKittenCardId = ektCardId;
        }
        break;

      case "defuse":
        // Remove exploding kitten from hand
        if (this.explodingKittenCardId) {
          const hand = this.playerHands.get(event.player) || [];
          const index = hand.indexOf(this.explodingKittenCardId);
          if (index !== -1) {
            hand.splice(index, 1);
            this.playerHands.set(event.player, hand);
            this.gameBoard.removeCard(this.explodingKittenCardId);
          }
          this.explodingKittenCardId = null;
        }
        // Also remove defuse card
        this.removeCardFromHand(event.player, "DEFUSE");
        const defuseHand = this.playerHands.get(event.player) || [];
        this.gameBoard.updatePlayerCards(event.player, defuseHand.length);
        // Update top card from the event
        if (event.top_card) {
          currentTopCard = event.top_card as CardType;
        }
        break;

      case "shuffle":
        // Update top card from the event (shuffle changes the top card)
        if (event.top_card) {
          currentTopCard = event.top_card as CardType;
        }
        break;

      case "discard_take":
        // Add card from discard to player's hand
        const dtHand = this.playerHands.get(event.player) || [];
        const dtCardId = `${event.player}-discard_take-${eventIndex}-${dtHand.length}`;
        const dtHandPos = this.gameBoard.getPlayerHandPosition(event.player, dtHand.length, dtHand.length + 1);
        this.gameBoard.createCard(event.card, dtHandPos, dtCardId);
        dtHand.push(dtCardId);
        this.playerHands.set(event.player, dtHand);
        this.gameBoard.updatePlayerCards(event.player, dtHand.length);
        break;

      case "card_steal":
        // Transfer the specific stolen card from victim to thief
        const victimHand = this.playerHands.get(event.victim) || [];
        if (victimHand.length > 0) {
          let stolenCardId: string | undefined;
          
          // If the replay specifies which card was stolen, find and remove that card
          if (event.stolen_card) {
            // Find a card of the stolen type in victim's hand
            const cardIndex = victimHand.findIndex(cardId => {
              const cardEl = this.gameBoard.getCardElement(cardId);
              if (!cardEl) {
                throw new Error(
                  `[AnimationController] getCardElement(${cardId}) returned null/undefined during card_steal. Victim: ${event.victim}, Thief: ${event.thief}, Looking for card type: ${event.stolen_card}, Event index: ${eventIndex}`
                );
              }
              return cardEl.cardType === event.stolen_card;
            });
            
            if (cardIndex !== -1) {
              stolenCardId = victimHand.splice(cardIndex, 1)[0];
            }
          }
          
          // Fallback: if no specific card was found, take the first card
          if (!stolenCardId && victimHand.length > 0) {
            stolenCardId = victimHand.splice(0, 1)[0];
          }
          
          if (stolenCardId) {
            const stolenCardElement = this.gameBoard.getCardElement(stolenCardId);
            this.playerHands.set(event.victim, victimHand);
            this.gameBoard.updatePlayerCards(event.victim, victimHand.length);
            
            // Add to thief's hand
            const thiefHand = this.playerHands.get(event.thief) || [];
            const thiefHandPos = this.gameBoard.getPlayerHandPosition(event.thief, thiefHand.length, thiefHand.length + 1);
            
            // Move card instantly to new position
            if (stolenCardElement) {
              stolenCardElement.element.style.left = `${thiefHandPos.x}px`;
              stolenCardElement.element.style.top = `${thiefHandPos.y}px`;
            }
            
            thiefHand.push(stolenCardId);
            this.playerHands.set(event.thief, thiefHand);
            this.gameBoard.updatePlayerCards(event.thief, thiefHand.length);
          }
        }
        break;

      case "card_request":
        // Move specific card from target to requester if successful
        if (event.success) {
          const targetHand = this.playerHands.get(event.target) || [];
          const cardIndex = this.findCardIndexByType(targetHand, event.requested_card);
          
          if (cardIndex !== -1) {
            const requestedCardId = targetHand[cardIndex];
            const requestedCardElement = this.gameBoard.getCardElement(requestedCardId);
            targetHand.splice(cardIndex, 1);
            this.playerHands.set(event.target, targetHand);
            this.gameBoard.updatePlayerCards(event.target, targetHand.length);
            
            // Add to requester's hand
            const requesterHand = this.playerHands.get(event.requester) || [];
            const requesterHandPos = this.gameBoard.getPlayerHandPosition(event.requester, requesterHand.length, requesterHand.length + 1);
            
            // Move card instantly to new position
            if (requestedCardElement) {
              requestedCardElement.element.style.left = `${requesterHandPos.x}px`;
              requestedCardElement.element.style.top = `${requesterHandPos.y}px`;
            }
            
            requesterHand.push(requestedCardId);
            this.playerHands.set(event.requester, requesterHand);
            this.gameBoard.updatePlayerCards(event.requester, requesterHand.length);
          }
        }
        break;

      case "favor":
        // Note: The actual card transfer happens via card_steal event that follows
        // This event just indicates the favor was played, no state change needed here
        break;

      case "game_end":
        this.clearHighlight();
        break;

      // Other events don't affect visual state
      default:
        break;
    }
    
    // Return the updated top card
    return currentTopCard;
  }

  /**
   * Helper to remove a card of specific type from player's hand
   */
  private removeCardFromHand(playerName: string, cardType: CardType): void {
    const playerHand = this.playerHands.get(playerName) || [];
    const cardIndex = this.findCardIndexByType(playerHand, cardType);
    
    if (cardIndex !== -1) {
      const cardId = playerHand[cardIndex];
      playerHand.splice(cardIndex, 1);
      this.playerHands.set(playerName, playerHand);
      this.gameBoard.removeCard(cardId);
    } else if (playerHand.length > 0) {
      // Determinism violation: card type not found in hand
      console.warn(
        `[Determinism violation] Tried to remove card of type ${cardType} from ${playerName}'s hand, but no such card was found. Hand: [${playerHand.join(", ")}]`
      );
      // Optionally, throw an error to enforce strict determinism:
      // throw new Error(`[Determinism violation] Tried to remove card of type ${cardType} from ${playerName}'s hand, but no such card was found.`);
    }
  }
}
