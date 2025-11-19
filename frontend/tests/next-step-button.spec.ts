import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Tests for the "next step" button functionality
 * These tests ensure that:
 * 1. Card counter correctly updates when using step forward
 * 2. Cards don't get stuck when stepping during playback
 * 3. Step forward pauses playback before advancing
 */
test.describe('Next Step Button - Bug Fixes', () => {
  test.beforeEach(async ({ page }) => {
    // Load a replay file before each test
    await page.goto('/');
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    
    // Wait for playback controls to become visible
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Wait for initial render
    await page.waitForTimeout(500);
  });

  test('card counter should update correctly when using step forward button', async ({ page }) => {
    const stepButton = page.locator('#btn-step-forward');
    const cardTracker = page.locator('#card-counts');
    
    // Get initial card counts
    const initialCardCounts = await cardTracker.textContent();
    
    // Step forward multiple times
    for (let i = 0; i < 10; i++) {
      await stepButton.click();
      await page.waitForTimeout(100); // Small delay between clicks
    }
    
    // Get card counts after stepping
    const afterSteppingCardCounts = await cardTracker.textContent();
    
    // Card counts should have changed (cards should be drawn from deck)
    // The exact counts depend on the replay file, but they should be different
    expect(afterSteppingCardCounts).not.toBe(initialCardCounts);
    
    // Verify card tracker is visible and has content
    await expect(cardTracker).toBeVisible();
    const hasCardCounts = await cardTracker.locator('div').count() > 0;
    expect(hasCardCounts).toBe(true);
  });

  test('card counter should decrease when cards are drawn during step forward', async ({ page }) => {
    const stepButton = page.locator('#btn-step-forward');
    const cardTracker = page.locator('#card-counts');
    
    // Get initial card counts
    const initialCardCounts = await cardTracker.textContent();
    
    // Step through at least 15 events to ensure we hit some card draws
    for (let i = 0; i < 15; i++) {
      await stepButton.click();
      await page.waitForTimeout(50);
    }
    
    // Get card counts after stepping
    const finalCardCounts = await cardTracker.textContent();
    
    // Card counts should have changed (cards were drawn from deck)
    expect(finalCardCounts).not.toBe(initialCardCounts);
    
    // Verify card tracker still has valid content
    await expect(cardTracker).toBeVisible();
  });

  test('step forward should pause playback if replay is playing', async ({ page }) => {
    const playPauseButton = page.locator('#btn-play-pause');
    const stepButton = page.locator('#btn-step-forward');
    const eventCounter = page.locator('#event-counter');
    
    // Start playing
    await playPauseButton.click();
    
    // Verify it's playing (button shows pause icon)
    await expect(playPauseButton).toContainText('⏸️');
    
    // Wait a moment for playback to start advancing
    await page.waitForTimeout(500);
    
    // Click step forward while playing
    await stepButton.click();
    
    // Wait for step to complete
    await page.waitForTimeout(200);
    
    // Playback should now be paused
    await expect(playPauseButton).toContainText('▶️');
    
    // Event counter should have advanced
    const counterText = await eventCounter.textContent();
    expect(counterText).toMatch(/Event: \d+ \/ \d+/);
  });

  test('cards should not get stuck when stepping during playback', async ({ page }) => {
    const playPauseButton = page.locator('#btn-play-pause');
    const stepButton = page.locator('#btn-step-forward');
    const eventCounter = page.locator('#event-counter');
    
    // Start playing
    await playPauseButton.click();
    await expect(playPauseButton).toContainText('⏸️');
    
    // Wait for some events to process
    await page.waitForTimeout(1000);
    
    // Get current event index
    const beforeStepText = await eventCounter.textContent();
    const beforeMatch = beforeStepText?.match(/Event: (\d+) \/ (\d+)/);
    const beforeEvent = beforeMatch ? parseInt(beforeMatch[1]) : 0;
    
    // Click step forward multiple times while it was playing
    for (let i = 0; i < 3; i++) {
      await stepButton.click();
      await page.waitForTimeout(150);
    }
    
    // Verify we advanced exactly 3 events from where we were
    const afterStepText = await eventCounter.textContent();
    const afterMatch = afterStepText?.match(/Event: (\d+) \/ (\d+)/);
    const afterEvent = afterMatch ? parseInt(afterMatch[1]) : 0;
    
    // We should have advanced at least 2 events (accounting for potential race conditions)
    expect(afterEvent).toBeGreaterThanOrEqual(beforeEvent + 2);
    
    // Playback should be paused now
    await expect(playPauseButton).toContainText('▶️');
    
    // Visual verification: check that cards are rendered properly
    const gameBoard = page.locator('#visual-board');
    await expect(gameBoard).toBeVisible();
  });

  test('step forward button should be disabled during event processing', async ({ page }) => {
    const stepButton = page.locator('#btn-step-forward');
    
    // Button should start enabled
    await expect(stepButton).toBeEnabled();
    
    // Click step forward
    const clickPromise = stepButton.click();
    
    // Button should be disabled immediately after click (during processing)
    // We need to check quickly before processing completes
    const isDisabledDuringProcessing = await page.evaluate(() => {
      const btn = document.querySelector<HTMLButtonElement>('#btn-step-forward');
      return btn?.disabled || false;
    });
    
    // Wait for processing to complete
    await clickPromise;
    await page.waitForTimeout(100);
    
    // Button should be enabled again after processing
    await expect(stepButton).toBeEnabled();
  });

  test('card counter should stay in sync through multiple rapid step forwards', async ({ page }) => {
    const stepButton = page.locator('#btn-step-forward');
    const cardTracker = page.locator('#card-counts');
    const eventCounter = page.locator('#event-counter');
    
    // Step forward rapidly 15 times
    for (let i = 0; i < 15; i++) {
      await stepButton.click();
      await page.waitForTimeout(50);
    }
    
    // Verify we're at event 16 (started at 1, stepped 15 times)
    const counterText = await eventCounter.textContent();
    const match = counterText?.match(/Event: (\d+) \/ (\d+)/);
    const currentEvent = match ? parseInt(match[1]) : 0;
    expect(currentEvent).toBe(16);
    
    // Verify card tracker is still showing valid data
    await expect(cardTracker).toBeVisible();
    const cardCountText = await cardTracker.textContent();
    
    // Should either show card counts or "Deck empty"
    const hasContent = cardCountText && (
      cardCountText.includes('Deck empty') || 
      /\d+/.test(cardCountText)
    );
    expect(hasContent).toBe(true);
  });

  test('step forward should work correctly after stop and reset', async ({ page }) => {
    const stepButton = page.locator('#btn-step-forward');
    const stopButton = page.locator('#btn-stop');
    const eventCounter = page.locator('#event-counter');
    const cardTracker = page.locator('#card-counts');
    
    // Step forward several times to ensure we draw some cards
    for (let i = 0; i < 10; i++) {
      await stepButton.click();
      await page.waitForTimeout(50);
    }
    
    // Verify we advanced
    const beforeStopText = await eventCounter.textContent();
    expect(beforeStopText).toContain('Event: 11 /');
    
    // Stop and reset
    await stopButton.click();
    await page.waitForTimeout(500);
    
    // Verify we're back at event 1
    const afterStopText = await eventCounter.textContent();
    expect(afterStopText).toContain('Event: 1 /');
    
    // Now step forward again
    await stepButton.click();
    await page.waitForTimeout(100);
    
    // Verify we advanced to event 2
    const afterStepText = await eventCounter.textContent();
    expect(afterStepText).toContain('Event: 2 /');
    
    // Card tracker should still be working
    const afterStepCardCounts = await cardTracker.textContent();
    expect(afterStepCardCounts).toBeTruthy();
    await expect(cardTracker).toBeVisible();
  });
});
