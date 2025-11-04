import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Replay Viewer - Agent Jump Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Load a replay file before each test
    await page.goto('/');
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to become visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
  });

  test('should have hidden agent jump input field', async ({ page }) => {
    const agentJumpInput = page.locator('#agent-jump-to-event');
    await expect(agentJumpInput).toBeAttached();
    
    // Should be hidden (type="hidden")
    const inputType = await agentJumpInput.getAttribute('type');
    expect(inputType).toBe('hidden');
  });

  test('should have data-testid for playwright access', async ({ page }) => {
    const agentJumpInput = page.getByTestId('agent-jump-to-event');
    await expect(agentJumpInput).toBeAttached();
  });

  test('should jump forward when valid target is set', async ({ page }) => {
    const agentJumpInput = page.getByTestId('agent-jump-to-event');
    const eventCounter = page.locator('#event-counter');
    
    // Get initial event index (should be "Event: 1 / X")
    const initialText = await eventCounter.textContent();
    expect(initialText).toContain('Event: 1 /');
    
    // Jump to event 5 (0-indexed, which is the 6th event)
    await agentJumpInput.evaluate((el: HTMLInputElement) => {
      el.value = '5';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });
    
    // Wait for event counter to update to event 6
    await expect(eventCounter).toContainText('Event: 6 /', { timeout: 2000 });
  });

  test('should not jump backward (safety check)', async ({ page }) => {
    const agentJumpInput = page.getByTestId('agent-jump-to-event');
    const stepButton = page.locator('#btn-step-forward');
    const eventCounter = page.locator('#event-counter');
    
    // Step forward a few times to get to event 4
    await stepButton.click();
    await page.waitForTimeout(300);
    await stepButton.click();
    await page.waitForTimeout(300);
    await stepButton.click();
    await page.waitForTimeout(300);
    
    // Wait for event counter to show event 4
    await expect(eventCounter).toContainText('Event: 4 /', { timeout: 2000 });
    
    // Try to jump backward to event 1 (should be ignored)
    await agentJumpInput.evaluate((el: HTMLInputElement) => {
      el.value = '1';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });
    
    // Wait a bit to ensure any potential async updates complete
    await page.waitForTimeout(500);
    
    // Should still be at event 4 (jump backward prevented)
    await expect(eventCounter).toContainText('Event: 4 /', { timeout: 1000 });
  });

  test('should handle jump to last event', async ({ page }) => {
    const agentJumpInput = page.getByTestId('agent-jump-to-event');
    const eventCounter = page.locator('#event-counter');
    
    // Get total number of events
    const initialText = await eventCounter.textContent();
    const match = initialText?.match(/Event: \d+ \/ (\d+)/);
    const totalEvents = match ? parseInt(match[1], 10) : 0;
    
    expect(totalEvents).toBeGreaterThan(0);
    
    // Jump to last event (0-indexed)
    const lastEventIndex = totalEvents - 1;
    await agentJumpInput.evaluate((el: HTMLInputElement, index: number) => {
      el.value = String(index);
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }, lastEventIndex);
    
    await page.waitForTimeout(500);
    
    // Should be at the last event
    const updatedText = await eventCounter.textContent();
    expect(updatedText).toContain(`Event: ${totalEvents} /`);
  });

  test('should ignore invalid jump values', async ({ page }) => {
    const agentJumpInput = page.getByTestId('agent-jump-to-event');
    const eventCounter = page.locator('#event-counter');
    
    // Get initial state
    const initialText = await eventCounter.textContent();
    
    // Try to set invalid value (non-numeric)
    await agentJumpInput.evaluate((el: HTMLInputElement) => {
      el.value = 'invalid';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });
    
    await page.waitForTimeout(500);
    
    // Should remain at initial position
    const currentText = await eventCounter.textContent();
    expect(currentText).toBe(initialText);
  });

  test('should ignore jump beyond max events', async ({ page }) => {
    const agentJumpInput = page.getByTestId('agent-jump-to-event');
    const eventCounter = page.locator('#event-counter');
    
    // Get total number of events
    const initialText = await eventCounter.textContent();
    const match = initialText?.match(/Event: \d+ \/ (\d+)/);
    const totalEvents = match ? parseInt(match[1], 10) : 0;
    
    // Try to jump way beyond the max
    const invalidIndex = totalEvents + 100;
    await agentJumpInput.evaluate((el: HTMLInputElement, index: number) => {
      el.value = String(index);
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }, invalidIndex);
    
    await page.waitForTimeout(500);
    
    // Should remain at initial position (event 1)
    const currentText = await eventCounter.textContent();
    expect(currentText).toContain('Event: 1 /');
  });

  test('should stop playback when jumping', async ({ page }) => {
    const agentJumpInput = page.getByTestId('agent-jump-to-event');
    const playPauseButton = page.locator('#btn-play-pause');
    
    // Start playing
    await playPauseButton.click();
    await expect(playPauseButton).toContainText('⏸️');
    
    // Jump to event 5
    await agentJumpInput.evaluate((el: HTMLInputElement) => {
      el.value = '5';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });
    
    await page.waitForTimeout(500);
    
    // Playback should be paused
    await expect(playPauseButton).toContainText('▶️');
  });
});
