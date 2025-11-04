/**
 * Unified system for special event animations
 * Provides reusable animation types for clearly showing player interactions
 */

import type { CardType } from "./types";
import { CARD_COLORS, DEFAULT_CARD_COLOR } from "./cardConfig";

/**
 * Configuration for transfer animations (stealing, giving, card requests)
 */
export interface TransferAnimationConfig {
  fromPlayer: string;
  toPlayer: string;
  card?: CardType;
  title: string;
  subtitle?: string;
  duration?: number;
}

/**
 * Configuration for target animations (attack, nope)
 */
export interface TargetAnimationConfig {
  sourcePlayer: string;
  targetPlayer: string;
  action: string;
  icon?: string;
  duration?: number;
}

/**
 * Configuration for showcase animations (see future, exploding kitten, defuse)
 */
export interface ShowcaseAnimationConfig {
  cards: CardType[];
  title: string;
  subtitle?: string;
  showExplosion?: boolean;
  duration?: number;
}

/**
 * Configuration for simple animations (shuffle)
 */
export interface SimpleAnimationConfig {
  element: HTMLElement;
  type: "shake" | "pulse" | "glow";
  duration?: number;
}

/**
 * Manages special event animations with a unified API
 */
export class SpecialEventAnimator {
  private overlayElement: HTMLElement | null = null;

  constructor(_container: HTMLElement) {
    this.createOverlay();
  }

  /**
   * Create the overlay element for displaying animations
   */
  private createOverlay(): void {
    this.overlayElement = document.createElement("div");
    this.overlayElement.id = "special-event-overlay";
    this.overlayElement.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.7);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      backdrop-filter: blur(4px);
    `;
    document.body.appendChild(this.overlayElement);
  }

  /**
   * Show a transfer animation (card/action moving from one player to another)
   */
  async showTransfer(config: TransferAnimationConfig): Promise<void> {
    if (!this.overlayElement) return;

    const duration = config.duration || 2500;
    const cardColor = config.card ? this.getCardColor(config.card) : "#888";
    const textColor = config.card ? this.getTextColor(cardColor) : "#000";
    const cardName = config.card ? this.formatCardName(config.card) : "a card";

    this.overlayElement.innerHTML = `
      <style>
        @keyframes slideFromLeft {
          from {
            transform: translateX(-150px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes slideFromRight {
          from {
            transform: translateX(150px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes cardTransfer {
          0% {
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            opacity: 1;
          }
          100% {
            left: 100%;
            top: 50%;
            transform: translateY(-50%);
            opacity: 1;
          }
        }
        @keyframes arrowPulse {
          0%, 100% {
            opacity: 0.6;
            transform: scale(1);
          }
          50% {
            opacity: 1;
            transform: scale(1.2);
          }
        }
      </style>
      <div style="
        background: rgba(0, 0, 0, 0.95);
        padding: 50px;
        border-radius: 24px;
        border: 4px solid #646cff;
        box-shadow: 0 0 60px rgba(100, 108, 255, 0.6);
        min-width: 600px;
        position: relative;
      ">
        <h2 style="
          color: #fff;
          text-align: center;
          margin: 0 0 20px 0;
          font-size: 24px;
          text-shadow: 0 0 15px rgba(100, 108, 255, 0.8);
        ">${this.escapeHtml(config.title)}</h2>
        ${config.subtitle ? `
          <p style="
            color: #aaa;
            text-align: center;
            margin: 0 0 30px 0;
            font-size: 14px;
          ">${this.escapeHtml(config.subtitle)}</p>
        ` : ''}
        
        <div style="
          display: flex;
          gap: 80px;
          align-items: center;
          justify-content: center;
          position: relative;
        ">
          <!-- Source Player -->
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            animation: slideFromLeft 0.5s ease forwards;
          ">
            <div style="
              width: 120px;
              height: 120px;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              border: 4px solid #fff;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 16px;
              font-weight: bold;
              color: #fff;
              text-align: center;
              padding: 10px;
              box-shadow: 0 8px 24px rgba(0,0,0,0.5);
            ">${this.escapeHtml(config.fromPlayer)}</div>
            <div style="color: #888; margin-top: 10px; font-size: 12px;">Giving</div>
          </div>
          
          <!-- Transfer visualization -->
          <div style="
            position: relative;
            width: 200px;
            height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <!-- Arrow -->
            <div style="
              position: absolute;
              width: 180px;
              height: 4px;
              background: linear-gradient(90deg, #646cff 0%, #ff6b6b 100%);
              border-radius: 2px;
              animation: arrowPulse 1.5s ease infinite;
            ">
              <div style="
                position: absolute;
                right: -10px;
                top: 50%;
                transform: translateY(-50%);
                width: 0;
                height: 0;
                border-left: 15px solid #ff6b6b;
                border-top: 10px solid transparent;
                border-bottom: 10px solid transparent;
              "></div>
            </div>
            
            <!-- Animated card -->
            ${config.card ? `
              <div style="
                position: absolute;
                left: 0;
                top: 50%;
                transform: translateY(-50%);
                width: 80px;
                height: 112px;
                background: ${cardColor};
                border: 2px solid #fff;
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
                animation: cardTransfer 1.5s ease infinite;
              ">${this.escapeHtml(cardName)}</div>
            ` : ''}
          </div>
          
          <!-- Target Player -->
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            animation: slideFromRight 0.5s ease forwards;
          ">
            <div style="
              width: 120px;
              height: 120px;
              background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
              border: 4px solid #fff;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 16px;
              font-weight: bold;
              color: #fff;
              text-align: center;
              padding: 10px;
              box-shadow: 0 8px 24px rgba(0,0,0,0.5);
            ">${this.escapeHtml(config.toPlayer)}</div>
            <div style="color: #888; margin-top: 10px; font-size: 12px;">Receiving</div>
          </div>
        </div>
      </div>
    `;

    this.overlayElement.style.display = "flex";
    await this.delay(duration);
    await this.hide();
  }

  /**
   * Show a target animation (player targeting/affecting another player)
   */
  async showTarget(config: TargetAnimationConfig): Promise<void> {
    if (!this.overlayElement) return;

    const duration = config.duration || 2000;
    const icon = config.icon || "⚡";

    this.overlayElement.innerHTML = `
      <style>
        @keyframes targetPulse {
          0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 20px rgba(255, 100, 100, 0.5);
          }
          50% {
            transform: scale(1.1);
            box-shadow: 0 0 40px rgba(255, 100, 100, 0.8);
          }
        }
        @keyframes iconBounce {
          0%, 100% {
            transform: translateY(0) scale(1);
          }
          50% {
            transform: translateY(-20px) scale(1.3);
          }
        }
        @keyframes beamShoot {
          from {
            width: 0;
            opacity: 1;
          }
          to {
            width: 200px;
            opacity: 0.8;
          }
        }
      </style>
      <div style="
        background: rgba(0, 0, 0, 0.95);
        padding: 50px;
        border-radius: 24px;
        border: 4px solid #ff6b6b;
        box-shadow: 0 0 60px rgba(255, 107, 107, 0.6);
        min-width: 600px;
      ">
        <h2 style="
          color: #ff6b6b;
          text-align: center;
          margin: 0 0 40px 0;
          font-size: 28px;
          text-shadow: 0 0 15px rgba(255, 107, 107, 0.9);
        ">${this.escapeHtml(config.action)}</h2>
        
        <div style="
          display: flex;
          gap: 100px;
          align-items: center;
          justify-content: center;
          position: relative;
        ">
          <!-- Source Player -->
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
          ">
            <div style="
              width: 140px;
              height: 140px;
              background: linear-gradient(135deg, #ffa07a 0%, #ff6347 100%);
              border: 4px solid #fff;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 18px;
              font-weight: bold;
              color: #fff;
              text-align: center;
              padding: 10px;
              box-shadow: 0 8px 24px rgba(0,0,0,0.5);
            ">${this.escapeHtml(config.sourcePlayer)}</div>
            <div style="color: #ff6b6b; margin-top: 10px; font-size: 14px; font-weight: bold;">Attacker</div>
          </div>
          
          <!-- Action Icon -->
          <div style="
            position: relative;
            width: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <!-- Energy beam -->
            <div style="
              position: absolute;
              left: 0;
              height: 6px;
              background: linear-gradient(90deg, #ff6b6b 0%, #ffa07a 100%);
              border-radius: 3px;
              animation: beamShoot 0.5s ease forwards;
              box-shadow: 0 0 20px rgba(255, 107, 107, 0.8);
            "></div>
            
            <div style="
              font-size: 64px;
              animation: iconBounce 1s ease infinite;
              filter: drop-shadow(0 0 20px rgba(255, 107, 107, 0.8));
            ">${icon}</div>
          </div>
          
          <!-- Target Player -->
          <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
          ">
            <div style="
              width: 140px;
              height: 140px;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              border: 4px solid #ff6b6b;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 18px;
              font-weight: bold;
              color: #fff;
              text-align: center;
              padding: 10px;
              box-shadow: 0 8px 24px rgba(0,0,0,0.5);
              animation: targetPulse 1s ease infinite;
            ">${this.escapeHtml(config.targetPlayer)}</div>
            <div style="color: #ff6b6b; margin-top: 10px; font-size: 14px; font-weight: bold;">Target</div>
          </div>
        </div>
      </div>
    `;

    this.overlayElement.style.display = "flex";
    await this.delay(duration);
    await this.hide();
  }

  /**
   * Show a showcase animation (prominently display cards or effects)
   */
  async showShowcase(config: ShowcaseAnimationConfig): Promise<void> {
    if (!this.overlayElement) return;

    const duration = config.duration || 2500;
    const cardElements = config.cards.map((cardType, index) => {
      const color = this.getCardColor(cardType);
      const textColor = this.getTextColor(color);
      const cardName = this.formatCardName(cardType);
      const offset = (index - (config.cards.length - 1) / 2) * 110;
      
      return `
        <div class="showcase-card" style="
          position: absolute;
          left: calc(50% + ${offset}px);
          transform: translateX(-50%);
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
          animation: showcaseCardAppear 0.3s ease forwards;
          animation-delay: ${index * 0.1}s;
          opacity: 0;
        ">${this.escapeHtml(cardName)}</div>
      `;
    }).join('');

    const explosionHTML = config.showExplosion ? `
      <div class="explosion" style="
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(255,100,0,0.8) 0%, rgba(255,0,0,0.4) 50%, transparent 70%);
        border-radius: 50%;
        animation: explode 0.8s ease-out forwards;
        pointer-events: none;
      "></div>
    ` : '';

    this.overlayElement.innerHTML = `
      <style>
        @keyframes showcaseCardAppear {
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
        background: rgba(0, 0, 0, 0.95);
        padding: 40px;
        border-radius: 20px;
        border: 4px solid #646cff;
        box-shadow: 0 0 60px rgba(100, 108, 255, 0.6);
      ">
        <h2 style="
          color: #fff;
          text-align: center;
          margin: 0 0 20px 0;
          font-size: 24px;
          text-shadow: 0 0 15px rgba(100, 108, 255, 0.8);
        ">${this.escapeHtml(config.title)}</h2>
        ${config.subtitle ? `
          <p style="
            color: #aaa;
            text-align: center;
            margin: 0 0 20px 0;
            font-size: 14px;
          ">${this.escapeHtml(config.subtitle)}</p>
        ` : ''}
        <div style="position: relative; height: 140px; width: 100%; display: flex; justify-content: center; align-items: center;">
          ${explosionHTML}
          ${cardElements}
        </div>
      </div>
    `;

    this.overlayElement.style.display = "flex";
    await this.delay(duration);
    await this.hide();
  }

  /**
   * Show a simple animation (quick visual feedback)
   */
  async showSimple(config: SimpleAnimationConfig): Promise<void> {
    const duration = config.duration || 800;
    const element = config.element;
    const originalTransition = element.style.transition;

    element.style.transition = "all 0.2s ease";

    switch (config.type) {
      case "shake":
        for (let i = 0; i < 3; i++) {
          element.style.transform = "rotate(10deg) scale(1.1)";
          await this.delay(100);
          element.style.transform = "rotate(-10deg) scale(1.1)";
          await this.delay(100);
        }
        element.style.transform = "rotate(0deg) scale(1)";
        break;

      case "pulse":
        for (let i = 0; i < 2; i++) {
          element.style.transform = "scale(1.2)";
          await this.delay(200);
          element.style.transform = "scale(1)";
          await this.delay(200);
        }
        break;

      case "glow":
        const originalBoxShadow = element.style.boxShadow;
        element.style.boxShadow = "0 0 30px rgba(100, 108, 255, 0.8)";
        await this.delay(duration);
        element.style.boxShadow = originalBoxShadow;
        break;
    }

    element.style.transition = originalTransition;
  }

  /**
   * Hide the overlay
   */
  async hide(): Promise<void> {
    if (!this.overlayElement) return;

    this.overlayElement.style.opacity = "1";
    this.overlayElement.style.transition = "opacity 0.3s ease";
    this.overlayElement.style.opacity = "0";
    
    await this.delay(300);
    this.overlayElement.style.display = "none";
    this.overlayElement.innerHTML = "";
    this.overlayElement.style.opacity = "1";
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
   * Format card name for display
   */
  private formatCardName(cardType: CardType | string): string {
    return cardType.replace(/_/g, " ");
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
   * Helper delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Cleanup the animator
   */
  destroy(): void {
    if (this.overlayElement) {
      this.overlayElement.remove();
      this.overlayElement = null;
    }
  }
}
