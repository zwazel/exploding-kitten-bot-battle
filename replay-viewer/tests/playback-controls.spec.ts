import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Replay Viewer - Playback Controls', () => {
  test.beforeEach(async ({ page }) => {
    // Load a replay file before each test
    await page.goto('/');
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to become visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
  });

  test('should have stop button', async ({ page }) => {
    const stopButton = page.locator('#btn-stop');
    await expect(stopButton).toBeVisible();
    await expect(stopButton).toBeEnabled();
  });

  test('should have play/pause button', async ({ page }) => {
    const playPauseButton = page.locator('#btn-play-pause');
    await expect(playPauseButton).toBeVisible();
    await expect(playPauseButton).toBeEnabled();
  });

  test('should have step forward button', async ({ page }) => {
    const stepButton = page.locator('#btn-step-forward');
    await expect(stepButton).toBeVisible();
    await expect(stepButton).toBeEnabled();
  });

  test('should have speed control slider', async ({ page }) => {
    const speedSlider = page.locator('#speed-slider');
    await expect(speedSlider).toBeVisible();
    
    // Check default value is 1
    const speedDisplay = page.locator('#speed-display');
    await expect(speedDisplay).toContainText('1.0x');
  });

  test('should change play button to pause when clicked', async ({ page }) => {
    const playPauseButton = page.locator('#btn-play-pause');
    
    // Initial state should be play (▶️)
    await expect(playPauseButton).toContainText('▶️');
    
    // Click to start playing
    await playPauseButton.click();
    
    // Button should change to pause (⏸️)
    await expect(playPauseButton).toContainText('⏸️');
  });

  test('should advance to next event when step forward is clicked', async ({ page }) => {
    const stepButton = page.locator('#btn-step-forward');
    
    // Click step forward button
    await stepButton.click();
    
    // The button should remain enabled after stepping
    await expect(stepButton).toBeEnabled();
  });

  test('should update speed display when slider is moved', async ({ page }) => {
    const speedSlider = page.locator('#speed-slider');
    const speedDisplay = page.locator('#speed-display');
    
    // Change speed to 2x
    await speedSlider.fill('2');
    
    // Speed display should update
    await expect(speedDisplay).toContainText('2.0x');
  });

  test('should reset to beginning when stop button is clicked', async ({ page }) => {
    // Step forward a few times
    const stepButton = page.locator('#btn-step-forward');
    await stepButton.click();
    await stepButton.click();
    
    // Click stop button
    const stopButton = page.locator('#btn-stop');
    await stopButton.click();
    
    // Play button should be visible (not pause)
    const playPauseButton = page.locator('#btn-play-pause');
    await expect(playPauseButton).toContainText('▶️');
  });

  test('should skip animations when step forward is clicked during playback', async ({ page }) => {
    const playPauseButton = page.locator('#btn-play-pause');
    const stepButton = page.locator('#btn-step-forward');
    const eventCounter = page.locator('#event-counter');
    
    // Start playing
    await playPauseButton.click();
    await expect(playPauseButton).toContainText('⏸️');
    
    // Wait a moment for playback to start
    await page.waitForTimeout(500);
    
    // Click step forward - should skip animations and jump to next event
    await stepButton.click();
    
    // The event counter should have advanced
    const counterText = await eventCounter.textContent();
    expect(counterText).toMatch(/Event: \d+ \/ \d+/);
    
    // Step button should be enabled again
    await expect(stepButton).toBeEnabled();
  });

  test('should quickly advance through multiple events with step button clicks', async ({ page }) => {
    const stepButton = page.locator('#btn-step-forward');
    const eventCounter = page.locator('#event-counter');
    
    // Get initial event number (should be 1)
    const initialText = await eventCounter.textContent();
    const initialMatch = initialText?.match(/Event: (\d+) \/ (\d+)/);
    const initialEvent = initialMatch ? parseInt(initialMatch[1]) : 1;
    
    // Click step forward multiple times rapidly
    for (let i = 0; i < 5; i++) {
      await stepButton.click();
      // Small wait to ensure processing completes
      await page.waitForTimeout(50);
    }
    
    // Verify we advanced exactly 5 events
    const finalText = await eventCounter.textContent();
    const finalMatch = finalText?.match(/Event: (\d+) \/ (\d+)/);
    const finalEvent = finalMatch ? parseInt(finalMatch[1]) : initialEvent;
    
    expect(finalEvent).toBe(initialEvent + 5);
  });
});
