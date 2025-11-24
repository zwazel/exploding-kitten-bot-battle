import { test, expect } from '@playwright/test';

test.describe('Replay Viewer - Basic UI', () => {
  test('renders the command center with dark chrome', async ({ page }) => {
    await page.goto('/');

    const title = page.locator('h1.app-title');
    await expect(title).toHaveText('Exploding Kittens Command Center');

    await expect(page.locator('h1')).toHaveCount(1);

    const shellBackground = await page.locator('.app-shell').evaluate((node) => {
      return window.getComputedStyle(node).backgroundColor;
    });
    expect(shellBackground).not.toMatch(/255, 255, 255/);
  });

  test('provides replay and bot tabs', async ({ page }) => {
    await page.goto('/');

    const tabs = page.locator('.app-nav .nav-btn');
    await expect(tabs).toHaveCount(2);
    await expect(tabs.nth(0)).toHaveText('Replay Viewer');
    await expect(tabs.nth(1)).toHaveText('Bots');
  });

  test('applies a dark site background', async ({ page }) => {
    await page.goto('/');
    const bodyColor = await page.evaluate(() => getComputedStyle(document.body).backgroundImage + getComputedStyle(document.body).backgroundColor);
    expect(bodyColor).not.toContain('rgb(255, 255, 255)');
  });

  test('should display file upload control', async ({ page }) => {
    await page.goto('/');

    // Check that the file input exists
    const fileInput = page.locator('#file-input');
    await expect(fileInput).toBeAttached();
    
    // Check that the file label is visible
    const fileLabel = page.locator('label[for="file-input"]');
    await expect(fileLabel).toBeVisible();
    await expect(fileLabel).toContainText('Load Replay File');
  });

  test('should hide playback controls initially', async ({ page }) => {
    await page.goto('/');
    
    // Playback controls should not be visible before loading a file
    const playbackControls = page.locator('#playback-controls');
    await expect(playbackControls).toBeHidden();
  });

  test('should have game display area', async ({ page }) => {
    await page.goto('/');

    // Check that the game display area exists
    const gameDisplay = page.locator('#game-display');
    await expect(gameDisplay).toBeAttached();
  });
});
