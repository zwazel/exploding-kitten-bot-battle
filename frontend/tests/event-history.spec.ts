import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Event History', () => {
  test('should show event history with latest events at top', async ({ page }) => {
    await page.goto('/');
    
    // Upload the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to be visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Check that event history section exists
    const historySection = page.locator('#event-history');
    await expect(historySection).toBeVisible();
    
    // Check that history content exists
    const historyContent = page.locator('#history-content');
    await expect(historyContent).toBeVisible();
    
    // After loading, should have at least one event (game_setup)
    const historyEntries = page.locator('.history-event-entry');
    const initialCount = await historyEntries.count();
    expect(initialCount).toBeGreaterThanOrEqual(1);
    
    // First entry should be Event 1 (game setup)
    const firstEntry = historyEntries.first();
    await expect(firstEntry).toContainText('Event 1');
    await expect(firstEntry).toContainText('Game started');
  });

  test('should add new events at the top when stepping forward', async ({ page }) => {
    await page.goto('/');
    
    // Upload the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Check initial event count
    const historyEntries = page.locator('.history-event-entry');
    const initialCount = await historyEntries.count();
    
    // Step forward
    const stepButton = page.locator('#btn-step-forward');
    await stepButton.click();
    await page.waitForTimeout(200);
    
    // Should have one more event
    const newCount = await historyEntries.count();
    expect(newCount).toBe(initialCount + 1);
    
    // The first (top) entry should now be Event 2
    const firstEntry = historyEntries.first();
    await expect(firstEntry).toContainText('Event 2');
    
    // Step forward again
    await stepButton.click();
    await page.waitForTimeout(200);
    
    // Should have another event
    const finalCount = await historyEntries.count();
    expect(finalCount).toBe(initialCount + 2);
    
    // The first (top) entry should now be Event 3
    await expect(historyEntries.first()).toContainText('Event 3');
  });

  test('should show all events up to current event', async ({ page }) => {
    await page.goto('/');
    
    // Upload the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Step forward 5 times
    const stepButton = page.locator('#btn-step-forward');
    for (let i = 0; i < 5; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
    }
    
    // Should have 6 events total (0-based, so 1 + 5 = 6)
    const historyEntries = page.locator('.history-event-entry');
    const count = await historyEntries.count();
    expect(count).toBe(6);
    
    // Verify events are in reverse order (newest first)
    const firstEntry = await historyEntries.first().textContent();
    const lastEntry = await historyEntries.last().textContent();
    
    expect(firstEntry).toContain('Event 6');
    expect(lastEntry).toContain('Event 1');
  });

  test('should reset history when stop button is clicked', async ({ page }) => {
    await page.goto('/');
    
    // Upload the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Step forward a few times
    const stepButton = page.locator('#btn-step-forward');
    for (let i = 0; i < 3; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
    }
    
    // Verify we have multiple events
    const historyEntries = page.locator('.history-event-entry');
    const countBeforeStop = await historyEntries.count();
    expect(countBeforeStop).toBeGreaterThan(1);
    
    // Click stop button
    const stopButton = page.locator('#btn-stop');
    await stopButton.click();
    
    // Wait for the event counter to update to indicate we're back at event 1
    await page.waitForFunction(() => {
      const counter = document.querySelector('#event-counter');
      return counter && counter.textContent && counter.textContent.includes('Event: 1 /');
    }, { timeout: 5000 });
    
    // Should be reset to Event 1 only
    const countAfterStop = await historyEntries.count();
    expect(countAfterStop).toBe(1);
    
    const firstEntry = historyEntries.first();
    await expect(firstEntry).toContainText('Event 1');
  });

  test('should be scrollable when many events are present', async ({ page }) => {
    await page.goto('/');
    
    // Upload the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Step forward many times to create more events than can fit
    const stepButton = page.locator('#btn-step-forward');
    for (let i = 0; i < 15; i++) {
      await stepButton.click();
      await page.waitForTimeout(50);
    }
    
    const historyContent = page.locator('#history-content');
    
    // Check that the history content has overflow (scrollable)
    const isScrollable = await historyContent.evaluate((el) => {
      return el.scrollHeight > el.clientHeight;
    });
    
    expect(isScrollable).toBeTruthy();
  });
});
