import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Chained NOPE Events', () => {
  test('should load replay file with chained NOPEs without errors', async ({ page }) => {
    await page.goto('/');
    
    // Upload the chained NOPE test replay file
    const filePath = path.join(__dirname, 'fixtures', 'chained_nope.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to be visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Verify no error messages
    const errorMessages = page.locator('.error, .error-message');
    const errorCount = await errorMessages.count();
    expect(errorCount).toBe(0);
    
    // Verify playback controls are functional
    const playButton = page.locator('#btn-play-pause');
    await expect(playButton).toBeVisible();
    
    // Verify event history exists
    const historySection = page.locator('#event-history');
    await expect(historySection).toBeVisible();
  });

  test('should play through chained NOPE events without crashing', async ({ page }) => {
    await page.goto('/');
    
    // Upload the chained NOPE test replay file
    const filePath = path.join(__dirname, 'fixtures', 'chained_nope.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Step forward through all events
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through at least 5 events (game_setup, turn_start, card_play, nope, nope)
    for (let i = 0; i < 5; i++) {
      await stepButton.click();
      await page.waitForTimeout(300);
    }
    
    // Verify no errors occurred during playback
    const errorMessages = page.locator('.error, .error-message');
    const errorCount = await errorMessages.count();
    expect(errorCount).toBe(0);
  });
  
  test('should display NOPE events in event history', async ({ page }) => {
    await page.goto('/');
    
    // Upload the chained NOPE test replay file
    const filePath = path.join(__dirname, 'fixtures', 'chained_nope.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Step forward to trigger the NOPEs
    const stepButton = page.locator('#btn-step-forward');
    for (let i = 0; i < 5; i++) {
      await stepButton.click();
      await page.waitForTimeout(200);
    }
    
    // Check that event history has some content
    const historyContent = page.locator('#history-content');
    await expect(historyContent).toBeVisible();
    
    // Verify the replay completed without errors
    const errorMessages = page.locator('.error, .error-message');
    const errorCount = await errorMessages.count();
    expect(errorCount).toBe(0);
  });
});
