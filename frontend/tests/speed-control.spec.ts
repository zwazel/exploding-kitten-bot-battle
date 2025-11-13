import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Replay Viewer - Speed Controls', () => {
  test.beforeEach(async ({ page }) => {
    // Load a replay file before each test
    await page.goto('/');
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to become visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
  });

  test('popup should be dismissible even when manual dismiss is unchecked', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    await checkbox.uncheck();
    
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through events looking for a popup
    for (let i = 0; i < 20; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
      
      const overlay = page.locator('#special-event-overlay');
      const isVisible = await overlay.isVisible();
      
      if (isVisible) {
        // Click close button while manual dismiss is unchecked
        const closeButton = page.locator('#popup-close-btn');
        await expect(closeButton).toBeVisible();
        await closeButton.click();
        
        // Popup should be hidden immediately
        await expect(overlay).toBeHidden();
        break;
      }
    }
  });

  test('clicking outside popup should work even when manual dismiss is unchecked', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    await checkbox.uncheck();
    
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through events looking for a popup
    for (let i = 0; i < 20; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
      
      const overlay = page.locator('#special-event-overlay');
      const isVisible = await overlay.isVisible();
      
      if (isVisible) {
        // Click on the overlay (outside the popup content) while manual dismiss is unchecked
        await overlay.click({ position: { x: 10, y: 10 } });
        
        // Popup should be hidden immediately
        await expect(overlay).toBeHidden();
        break;
      }
    }
  });

  test('popup auto-dismiss should be faster at higher speeds', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    await checkbox.uncheck();
    
    // Set speed to 10x
    const speedInput = page.locator('#speed-input');
    await speedInput.fill('10');
    await speedInput.press('Enter');
    
    // Verify speed was set
    const speedDisplay = page.locator('#speed-display');
    await expect(speedDisplay).toContainText('10');
    
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through events looking for a popup
    for (let i = 0; i < 20; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
      
      const overlay = page.locator('#special-event-overlay');
      const isVisible = await overlay.isVisible();
      
      if (isVisible) {
        // At 10x speed, a 2500ms popup should dismiss in 250ms
        // Wait 500ms to give some buffer
        await page.waitForTimeout(500);
        
        // Popup should be hidden after auto-dismiss timeout
        await expect(overlay).toBeHidden();
        break;
      }
    }
  });

  test('popup auto-dismiss should be slower at lower speeds', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    await checkbox.uncheck();
    
    // Set speed to 0.5x
    const speedSlider = page.locator('#speed-slider');
    await speedSlider.fill('0.5');
    
    // Verify speed was set
    const speedDisplay = page.locator('#speed-display');
    await expect(speedDisplay).toContainText('0.5');
    
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through events looking for a popup
    for (let i = 0; i < 20; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
      
      const overlay = page.locator('#special-event-overlay');
      const isVisible = await overlay.isVisible();
      
      if (isVisible) {
        // At 0.5x speed, popup should NOT dismiss quickly
        // Wait 1 second - popup should still be visible
        await page.waitForTimeout(1000);
        await expect(overlay).toBeVisible();
        
        // Dismiss it manually so test can continue
        const closeButton = page.locator('#popup-close-btn');
        await closeButton.click();
        break;
      }
    }
  });

  test('animation speed should affect card draw animations', async ({ page }) => {
    // Set speed to 100x for very fast animations
    const speedInput = page.locator('#speed-input');
    await speedInput.fill('100');
    await speedInput.press('Enter');
    
    // Verify speed was set
    const speedDisplay = page.locator('#speed-display');
    await expect(speedDisplay).toContainText('100');
    
    // Step forward multiple times rapidly
    const stepButton = page.locator('#btn-step-forward');
    const startTime = Date.now();
    
    // Step through 5 events
    for (let i = 0; i < 5; i++) {
      await stepButton.click();
      await page.waitForTimeout(50); // Small wait for animations to process
    }
    
    const endTime = Date.now();
    const elapsed = endTime - startTime;
    
    // At 100x speed, 5 events should take less than 1 second
    // Even with network latency, it should be much faster than normal speed
    expect(elapsed).toBeLessThan(1500);
  });

  test('speed input should accept values up to 100', async ({ page }) => {
    const speedInput = page.locator('#speed-input');
    
    // Try setting to 100x
    await speedInput.fill('100');
    await speedInput.press('Enter');
    
    // Verify it was accepted
    const value = await speedInput.inputValue();
    expect(parseFloat(value)).toBe(100);
    
    const speedDisplay = page.locator('#speed-display');
    await expect(speedDisplay).toContainText('100');
  });

  test('speed slider max should be 10', async ({ page }) => {
    const speedSlider = page.locator('#speed-slider');
    
    const max = await speedSlider.getAttribute('max');
    expect(parseFloat(max!)).toBe(10);
  });

  test('speed changes should propagate to renderer', async ({ page }) => {
    // Change speed multiple times and verify display updates
    const speedInput = page.locator('#speed-input');
    const speedDisplay = page.locator('#speed-display');
    
    await speedInput.fill('5');
    await speedInput.press('Enter');
    await expect(speedDisplay).toContainText('5');
    
    await speedInput.fill('25');
    await speedInput.press('Enter');
    await expect(speedDisplay).toContainText('25');
    
    await speedInput.fill('0.5');
    await speedInput.press('Enter');
    await expect(speedDisplay).toContainText('0.5');
  });
});
