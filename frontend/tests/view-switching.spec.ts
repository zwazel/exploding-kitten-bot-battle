import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const replayFixture = path.join(__dirname, 'fixtures', 'test_replay.json');

test.describe('View switching behaviour', () => {
  test('pauses playback and keeps layout stable when visiting bots view', async ({ page }) => {
    await page.goto('/');
    await page.locator('#file-input').setInputFiles(replayFixture);
    await page.locator('#playback-controls').waitFor({ state: 'visible' });

    // Start playback and capture a frame count.
    await page.locator('#btn-play-pause').click();
    await page.waitForTimeout(600);
    const beforeSwitch = (await page.locator('#event-counter').textContent()) ?? '';

    // Switch to bots view and wait briefly.
    await page.locator('button[data-view="bots"]').click();
    await page.waitForTimeout(400);

    // Switch back to replay viewer.
    await page.locator('button[data-view="viewer"]').click();

    // Playback should now be paused and the event counter should not have advanced.
    const afterSwitch = (await page.locator('#event-counter').textContent()) ?? '';
    await expect(page.locator('#btn-play-pause')).toHaveText('▶️');
    expect(afterSwitch).toBe(beforeSwitch);

    // The board should still be centered after the view swap.
    const boardBounds = await page.locator('.game-board').boundingBox();
    const shellBounds = await page.locator('.visual-board-shell').boundingBox();
    expect(boardBounds).not.toBeNull();
    expect(shellBounds).not.toBeNull();
    const boardCenter = boardBounds!.x + boardBounds!.width / 2;
    const shellCenter = shellBounds!.x + shellBounds!.width / 2;
    expect(Math.abs(boardCenter - shellCenter)).toBeLessThanOrEqual(6);
  });
});
