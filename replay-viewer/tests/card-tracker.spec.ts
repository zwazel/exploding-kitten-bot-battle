import { test, expect } from '@playwright/test';
import * as path from 'path';

test('card tracker displays and updates', async ({ page }) => {
  // Start the dev server first
  await page.goto('http://localhost:5173');
  
  // Wait for the page to load
  await expect(page.locator('h1')).toContainText('Exploding Kittens Replay Viewer');
  
  // Upload the replay file
  const fileInput = page.locator('#file-input');
  await fileInput.setInputFiles('/tmp/test_replay.json');
  
  // Wait for the replay to load
  await page.waitForTimeout(2000);
  
  // Check that the card tracker is visible
  await expect(page.locator('#card-tracker')).toBeVisible();
  await expect(page.locator('#card-tracker h3')).toContainText('Cards in Deck');
  
  // Check that card counts are displayed
  const cardCounts = page.locator('#card-counts');
  await expect(cardCounts).toBeVisible();
  
  // Take a screenshot of the initial state
  await page.screenshot({ path: '/tmp/card-tracker-initial.png', fullPage: true });
  
  // Step forward a few times
  const stepButton = page.locator('#btn-step-forward');
  await stepButton.click();
  await page.waitForTimeout(1000);
  await stepButton.click();
  await page.waitForTimeout(1000);
  await stepButton.click();
  await page.waitForTimeout(1000);
  
  // Take a screenshot after stepping
  await page.screenshot({ path: '/tmp/card-tracker-after-steps.png', fullPage: true });
});
