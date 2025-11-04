import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Replay Viewer - File Upload', () => {
  test('should load a replay file and show playback controls', async ({ page }) => {
    await page.goto('/');
    
    // Upload the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait a moment for the file to be processed
    await page.waitForTimeout(500);
    
    // Check that the file name is displayed
    const fileName = page.locator('#file-name');
    await expect(fileName).toContainText('test_replay.json');
    
    // Check that playback controls are now visible
    const playbackControls = page.locator('#playback-controls');
    await expect(playbackControls).toBeVisible();
  });

  test('should display game metadata after loading replay', async ({ page }) => {
    await page.goto('/');
    
    // Upload the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for the file to be processed
    await page.waitForTimeout(500);
    
    // Check that game display shows some content
    const gameDisplay = page.locator('#game-display');
    await expect(gameDisplay).not.toBeEmpty();
  });
});
