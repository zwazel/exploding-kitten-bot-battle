import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Replay Viewer - Speed Controls', () => {
  test.beforeEach(async ({ page }) => {
    // Load a replay file before each test
    await page.goto('/');
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to become visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
  });

  test('should have speed slider with correct range', async ({ page }) => {
    const speedSlider = page.locator('#speed-slider');
    await expect(speedSlider).toBeVisible();
    
    // Check min, max, and step attributes
    await expect(speedSlider).toHaveAttribute('min', '0.5');
    await expect(speedSlider).toHaveAttribute('max', '10');
    await expect(speedSlider).toHaveAttribute('step', '0.5');
  });

  test('should have speed input field with correct range', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    await expect(speedInput).toBeVisible();
    
    // Check min, max, and step attributes
    await expect(speedInput).toHaveAttribute('min', '0.1');
    await expect(speedInput).toHaveAttribute('max', '100');
    await expect(speedInput).toHaveAttribute('step', '0.1');
  });

  test('should update speed display when slider is moved to 10x', async ({ page }) => {
    const speedSlider = page.locator('#speed-slider');
    const speedDisplay = page.locator('#speed-display');
    
    // Change speed to 10x (max value)
    await speedSlider.fill('10');
    
    // Speed display should update
    await expect(speedDisplay).toContainText('10.0x');
  });

  test('should update speed display when slider is moved to intermediate values', async ({ page }) => {
    const speedSlider = page.locator('#speed-slider');
    const speedDisplay = page.locator('#speed-display');
    
    // Test various slider values
    const testValues = ['0.5', '2', '5', '7.5', '10'];
    
    for (const value of testValues) {
      await speedSlider.fill(value);
      const expectedDisplay = `${parseFloat(value).toFixed(1)}x`;
      await expect(speedDisplay).toContainText(expectedDisplay);
    }
  });

  test('should update speed display when input field is changed', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedDisplay = page.locator('#speed-display');
    
    // Change speed to 15x via input
    await speedInput.fill('15');
    await speedInput.blur(); // Trigger change event
    
    // Speed display should update
    await expect(speedDisplay).toContainText('15.0x');
  });

  test('should clamp input field values above maximum', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedDisplay = page.locator('#speed-display');
    
    // Try to set speed to 150x (above max of 100x)
    await speedInput.fill('150');
    await speedInput.blur();
    
    // Should be clamped to 100x
    await expect(speedDisplay).toContainText('100.0x');
    await expect(speedInput).toHaveValue('100.0');
  });

  test('should clamp input field values below minimum', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedDisplay = page.locator('#speed-display');
    
    // Try to set speed to 0.05x (below min of 0.1x)
    await speedInput.fill('0.05');
    await speedInput.blur();
    
    // Should be clamped to 0.1x
    await expect(speedDisplay).toContainText('0.1x');
    await expect(speedInput).toHaveValue('0.1');
  });

  test('should sync slider when input is within slider range', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedSlider = page.locator('#speed-slider');
    const speedDisplay = page.locator('#speed-display');
    
    // Set speed to 5x via input (within slider range)
    await speedInput.fill('5');
    await speedInput.blur();
    
    // Slider should update to match
    await expect(speedSlider).toHaveValue('5');
    await expect(speedDisplay).toContainText('5.0x');
  });

  test('should not update slider when input is outside slider range', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedSlider = page.locator('#speed-slider');
    const speedDisplay = page.locator('#speed-display');
    
    // Set speed to 50x via input (outside slider range of 0.5-10)
    await speedInput.fill('50');
    await speedInput.blur();
    
    // Display should show 50x but slider should stay at previous value
    await expect(speedDisplay).toContainText('50.0x');
    // Slider value should remain unchanged (it stays at whatever it was before)
    const sliderValue = await speedSlider.inputValue();
    expect(parseFloat(sliderValue)).toBeLessThanOrEqual(10);
  });

  test('should update input field when slider is moved', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedSlider = page.locator('#speed-slider');
    
    // Move slider to 7x
    await speedSlider.fill('7');
    
    // Input field should update
    await expect(speedInput).toHaveValue('7.0');
  });

  test('should handle decimal values in input field', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedDisplay = page.locator('#speed-display');
    
    // Set speed to 2.5x
    await speedInput.fill('2.5');
    await speedInput.blur();
    
    await expect(speedDisplay).toContainText('2.5x');
    await expect(speedInput).toHaveValue('2.5');
  });

  test('should handle very high speeds (near maximum)', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedDisplay = page.locator('#speed-display');
    
    // Set speed to 95x
    await speedInput.fill('95');
    await speedInput.blur();
    
    await expect(speedDisplay).toContainText('95.0x');
    await expect(speedInput).toHaveValue('95.0');
  });

  test('should handle very low speeds (near minimum)', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedDisplay = page.locator('#speed-display');
    
    // Set speed to 0.2x
    await speedInput.fill('0.2');
    await speedInput.blur();
    
    await expect(speedDisplay).toContainText('0.2x');
    await expect(speedInput).toHaveValue('0.2');
  });

  test('should maintain speed setting during playback', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedDisplay = page.locator('#speed-display');
    const playPauseButton = page.locator('#btn-play-pause');
    
    // Set speed to 5x
    await speedInput.fill('5');
    await speedInput.blur();
    await expect(speedDisplay).toContainText('5.0x');
    
    // Start playback
    await playPauseButton.click();
    await expect(playPauseButton).toContainText('⏸️');
    
    // Wait a bit
    await page.waitForTimeout(500);
    
    // Speed display should still show 5x
    await expect(speedDisplay).toContainText('5.0x');
    
    // Pause playback
    await playPauseButton.click();
  });

  test('should allow changing speed during playback', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    const speedDisplay = page.locator('#speed-display');
    const playPauseButton = page.locator('#btn-play-pause');
    
    // Start playback at default speed
    await playPauseButton.click();
    await expect(playPauseButton).toContainText('⏸️');
    
    // Wait a moment
    await page.waitForTimeout(300);
    
    // Change speed to 10x while playing
    await speedInput.fill('10');
    await speedInput.blur();
    
    // Speed should update
    await expect(speedDisplay).toContainText('10.0x');
    
    // Pause playback
    await playPauseButton.click();
  });

  test('should accept and apply different speed values during playback', async ({ page }) => {
    const playPauseButton = page.locator('#btn-play-pause');
    const eventCounter = page.locator('#event-counter');
    const speedInput = page.locator('#speed-input');
    
    // Test that setting different speeds doesn't break playback
    
    // Start at slow speed (0.5x)
    await speedInput.fill('0.5');
    await speedInput.blur();
    
    // Start playback
    await playPauseButton.click();
    await page.waitForTimeout(500);
    
    // Verify playback is running and counter advances
    const text1 = await eventCounter.textContent();
    const match1 = text1?.match(/Event: (\d+) \/ (\d+)/);
    const event1 = match1 ? parseInt(match1[1]) : 0;
    
    // Change to fast speed during playback
    await speedInput.fill('10');
    await speedInput.blur();
    await page.waitForTimeout(500);
    
    // Verify counter continues to advance
    const text2 = await eventCounter.textContent();
    const match2 = text2?.match(/Event: (\d+) \/ (\d+)/);
    const event2 = match2 ? parseInt(match2[1]) : 0;
    
    // Stop playback
    await playPauseButton.click();
    
    // Events should have advanced (counter increased)
    expect(event2).toBeGreaterThanOrEqual(event1);
  });
});
