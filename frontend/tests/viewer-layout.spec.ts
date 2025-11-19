import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const replayFixture = path.join(__dirname, 'fixtures', 'test_replay.json');

test.describe('Replay viewer layout polish', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.locator('#file-input').setInputFiles(replayFixture);
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
  });

  test('keeps playback controls anchored above the replay canvas', async ({ page }) => {
    const controlsBox = await page.locator('#playback-controls').boundingBox();
    const displayBox = await page.locator('#game-display').boundingBox();

    expect(controlsBox).not.toBeNull();
    expect(displayBox).not.toBeNull();

    // Playback controls should appear above the game display area with a small margin.
    const controlsBottom = (controlsBox!.y + controlsBox!.height);
    const displayTop = displayBox!.y;
    expect(controlsBottom).toBeLessThanOrEqual(displayTop + 12);
  });

  test('renders legends outside of the replay canvas', async ({ page }) => {
    const isCardTrackerInside = await page.evaluate(() => {
      const tracker = document.querySelector('#card-tracker');
      const canvas = document.querySelector('#game-display');
      return tracker && canvas ? canvas.contains(tracker) : false;
    });
    expect(isCardTrackerInside).toBeFalsy();

    const isLegendInside = await page.evaluate(() => {
      const legend = document.querySelector('#color-legend');
      const canvas = document.querySelector('#game-display');
      return legend && canvas ? canvas.contains(legend) : false;
    });
    expect(isLegendInside).toBeFalsy();
  });

  test('centers the board inside the visual shell', async ({ page }) => {
    const boardBounds = await page.locator('.game-board').boundingBox();
    const shellBounds = await page.locator('.visual-board-shell').boundingBox();

    expect(boardBounds).not.toBeNull();
    expect(shellBounds).not.toBeNull();

    const boardCenterX = boardBounds!.x + boardBounds!.width / 2;
    const shellCenterX = shellBounds!.x + shellBounds!.width / 2;

    expect(Math.abs(boardCenterX - shellCenterX)).toBeLessThanOrEqual(4);
  });

  test('positions event history beneath the visual board', async ({ page }) => {
    const shellBounds = await page.locator('.visual-board-shell').boundingBox();
    const historyBounds = await page.locator('#event-history').boundingBox();

    expect(shellBounds).not.toBeNull();
    expect(historyBounds).not.toBeNull();

    const historyTop = historyBounds!.y;
    const shellBottom = shellBounds!.y + shellBounds!.height;
    expect(historyTop).toBeGreaterThan(shellBottom - 5);
  });
});
