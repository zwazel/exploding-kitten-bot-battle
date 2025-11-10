import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Replay Viewer - File Upload', () => {
  test('should load a replay file and show playback controls', async ({ page }) => {
    await page.goto('/');
    
    // Upload the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
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
    
    // Wait for playback controls to be visible (indicates file is loaded)
    await page.locator('#playback-controls').waitFor({ state: 'visible' });
    
    // Check that game display shows some content
    const gameDisplay = page.locator('#game-display');
    await expect(gameDisplay).not.toBeEmpty();
  });
});
