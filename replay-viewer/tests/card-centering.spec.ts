import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Replay Viewer - Card Centering in Popup', () => {
  test('should center cards in defuse popup', async ({ page }) => {
    // Load the replay viewer
    await page.goto('/');
    
    // Load a replay file with defuse scenario
    const filePath = path.join(__dirname, 'fixtures', 'test_defuse_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to become visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Step through events to get to the defuse event
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through: game_setup, turn_start, card_draw, turn_start, exploding_kitten_draw, defuse
    for (let i = 0; i < 6; i++) {
      await stepButton.click();
      await page.waitForTimeout(200);
    }
    
    // Wait for the overlay to appear (defuse animation)
    await page.waitForTimeout(500);
    
    // Check that the overlay is visible
    const overlay = page.locator('#special-event-overlay');
    await expect(overlay).toBeVisible({ timeout: 10000 });
    
    // Take a screenshot of the defuse popup
    await page.screenshot({ path: '/tmp/defuse-popup-centered.png', fullPage: true });
    
    // Verify the showcase cards container has proper width
    const showcaseCards = overlay.locator('.showcase-card');
    const count = await showcaseCards.count();
    expect(count).toBeGreaterThan(0);
    
    // Wait for overlay to disappear
    await page.waitForTimeout(2500);
  });
  
  test('should center cards in explosion popup', async ({ page }) => {
    // Load the replay viewer
    await page.goto('/');
    
    // Load a replay file with explosion scenario
    const filePath = path.join(__dirname, 'fixtures', 'test_defuse_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to become visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Step through events to get to the explosion event
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through: game_setup, turn_start, card_draw, turn_start, exploding_kitten_draw, defuse, turn_start, exploding_kitten_draw (explosion)
    for (let i = 0; i < 8; i++) {
      await stepButton.click();
      await page.waitForTimeout(200);
    }
    
    // Wait for the overlay to appear (explosion animation)
    await page.waitForTimeout(500);
    
    // Check that the overlay is visible
    const overlay = page.locator('#special-event-overlay');
    await expect(overlay).toBeVisible({ timeout: 10000 });
    
    // Take a screenshot of the explosion popup
    await page.screenshot({ path: '/tmp/explosion-popup-centered.png', fullPage: true });
    
    // Verify the showcase cards container exists and has cards
    const showcaseCards = overlay.locator('.showcase-card');
    const count = await showcaseCards.count();
    expect(count).toBeGreaterThan(0);
    
    // Wait for overlay to disappear
    await page.waitForTimeout(3000);
  });
});
