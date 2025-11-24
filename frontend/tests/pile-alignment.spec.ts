import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const CARD_WIDTH = 80;
const CARD_HEIGHT = 112;

function toBeApproximately(received: number, expected: number, threshold = 1.5) {
  expect(Math.abs(received - expected)).toBeLessThanOrEqual(threshold);
}

test.describe('Deck and discard piles alignment', () => {
  test('visual piles line up with animated card positions', async ({ page }) => {
    await page.goto('/');

    const filePath = path.join(__dirname, 'fixtures', 'simple-game.json');
    await page.locator('#file-input').setInputFiles(filePath);

    await page.waitForSelector('#deck-pile');

    const alignment = await page.evaluate(({ cardWidth }) => {
      const deckElement = document.querySelector('#deck-pile');
      const discardElement = document.querySelector('#discard-pile');
      const gameBoard = (globalThis as Record<string, unknown>).__EK_REPLAY_GAME_BOARD__ as { getPilePositionsForTesting: () => { deck: { x: number; y: number }; discard: { x: number; y: number } } } | undefined;

      if (!deckElement || !discardElement || !gameBoard) {
        throw new Error('Required elements were not found');
      }

      const piles = gameBoard.getPilePositionsForTesting();

      return {
        deckCardCenter: piles.deck.x + cardWidth / 2,
        discardCardCenter: piles.discard.x + cardWidth / 2,
        tableCenter: 1200 / 2,
        debug: {
          piles: {
            deck: { ...piles.deck },
            discard: { ...piles.discard },
          },
          styles: {
            deckLeft: deckElement.style.left,
            discardLeft: discardElement.style.left,
            deckTop: deckElement.style.top,
            discardTop: discardElement.style.top,
          },
        },
      };
    }, { cardWidth: CARD_WIDTH });

    const pileWidth = 100;
    const pileHeight = 140;

    const deckLeft = parseFloat(alignment.debug.styles.deckLeft);
    const discardLeft = parseFloat(alignment.debug.styles.discardLeft);
    const deckTop = parseFloat(alignment.debug.styles.deckTop);
    const discardTop = parseFloat(alignment.debug.styles.discardTop);

    toBeApproximately(deckLeft + pileWidth / 2, alignment.deckCardCenter);
    toBeApproximately(discardLeft + pileWidth / 2, alignment.discardCardCenter);
    toBeApproximately(deckTop + pileHeight / 2, alignment.debug.piles.deck.y + CARD_HEIGHT / 2);
    toBeApproximately(discardTop + pileHeight / 2, alignment.debug.piles.discard.y + CARD_HEIGHT / 2);

    // Midpoint of the two piles should be the table center so the whole stack appears centered.
    const midpoint = (alignment.deckCardCenter + alignment.discardCardCenter) / 2;
    toBeApproximately(midpoint, alignment.tableCenter, 1.5);
  });
});
