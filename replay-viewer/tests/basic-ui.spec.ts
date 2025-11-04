import { test, expect } from '@playwright/test';

test.describe('Replay Viewer - Basic UI', () => {
  test('should load the page successfully', async ({ page }) => {
    await page.goto('/');
    
    // Check that the page title is correct
    await expect(page).toHaveTitle(/Exploding Kittens Replay Viewer/);
    
    // Check that the main heading is visible
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('Exploding Kittens Replay Viewer');
  });

  test('should display file upload control', async ({ page }) => {
    await page.goto('/');
    
    // Check that the file input exists
    const fileInput = page.locator('input[type="file"]');
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
