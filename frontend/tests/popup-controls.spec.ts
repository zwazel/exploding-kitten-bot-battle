import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Replay Viewer - Popup Controls', () => {
  test.beforeEach(async ({ page }) => {
    // Load a replay file before each test
    await page.goto('/');
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to become visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
  });

  test('should have manual popup dismiss checkbox', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    await expect(checkbox).toBeVisible();
    await expect(checkbox).toBeEnabled();
  });

  test('manual popup dismiss checkbox should be checked by default', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    await expect(checkbox).toBeChecked();
  });

  test('should be able to toggle manual popup dismiss checkbox', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    
    // Initially checked
    await expect(checkbox).toBeChecked();
    
    // Uncheck it
    await checkbox.uncheck();
    await expect(checkbox).not.toBeChecked();
    
    // Check it again
    await checkbox.check();
    await expect(checkbox).toBeChecked();
  });

  test('popup should have close button when displayed', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    await checkbox.check();
    
    // Use agent jump to quickly get to an event with a popup
    // Jump to an event that triggers a popup (e.g., attack or favor)
    const jumpInput = page.getByTestId('agent-jump-to-event');
    
    // Look through events to find one that would trigger a popup
    // For now, we'll step through a few events
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through events looking for a popup
    for (let i = 0; i < 20; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
      
      // Check if overlay is visible
      const overlay = page.locator('#special-event-overlay');
      const isVisible = await overlay.isVisible();
      
      if (isVisible) {
        // Check for close button
        const closeButton = page.locator('#popup-close-btn');
        await expect(closeButton).toBeVisible();
        
        // Click close button to dismiss
        await closeButton.click();
        
        // Popup should be hidden
        await expect(overlay).toBeHidden();
        break;
      }
    }
  });

  test('clicking outside popup should close it', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    await checkbox.check();
    
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through events looking for a popup
    for (let i = 0; i < 20; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
      
      const overlay = page.locator('#special-event-overlay');
      const isVisible = await overlay.isVisible();
      
      if (isVisible) {
        // Click on the overlay (outside the popup content)
        await overlay.click({ position: { x: 10, y: 10 } });
        
        // Popup should be hidden
        await expect(overlay).toBeHidden();
        break;
      }
    }
  });

  test('popup should auto-dismiss when checkbox is unchecked', async ({ page }) => {
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
        // Wait a bit and check if popup auto-dismisses
        await page.waitForTimeout(3000);
        
        // Popup should be hidden after auto-dismiss timeout
        await expect(overlay).toBeHidden();
        break;
      }
    }
  });

  test('close button X should be styled correctly', async ({ page }) => {
    const checkbox = page.locator('#manual-popup-dismiss');
    await checkbox.check();
    
    const stepButton = page.locator('#btn-step-forward');
    
    // Step through events looking for a popup
    for (let i = 0; i < 20; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
      
      const overlay = page.locator('#special-event-overlay');
      const isVisible = await overlay.isVisible();
      
      if (isVisible) {
        const closeButton = page.locator('#popup-close-btn');
        await expect(closeButton).toBeVisible();
        
        // Check button content
        await expect(closeButton).toContainText('✕');
        
        // Check title attribute
        const title = await closeButton.getAttribute('title');
        expect(title).toContain('Close');
        
        // Dismiss popup
        await closeButton.click();
        break;
      }
    }
  });
});
