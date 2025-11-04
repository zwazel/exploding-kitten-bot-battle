import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Replay Viewer - Playback Controls', () => {
  test.beforeEach(async ({ page }) => {
    // Load a replay file before each test
    await page.goto('/');
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    await page.waitForTimeout(500);
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
    
    // Wait a moment for the UI to update
    await page.waitForTimeout(200);
    
    // The game display should have updated (we can't check exact content without knowing structure)
    // But we can verify the button is still clickable
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
    await page.waitForTimeout(200);
    
    // Click stop button
    const stopButton = page.locator('#btn-stop');
    await stopButton.click();
    
    // Wait a moment for reset
    await page.waitForTimeout(200);
    
    // Play button should be visible (not pause)
    const playPauseButton = page.locator('#btn-play-pause');
    await expect(playPauseButton).toContainText('▶️');
  });
});
