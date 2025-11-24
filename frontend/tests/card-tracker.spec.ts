import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test('card tracker displays and updates', async ({ page }) => {
  // Start the dev server first
  await page.goto('/');
  
  // Wait for the page to load
  await expect(page.getByRole('heading', { name: 'Exploding Kittens Command Center' })).toBeVisible();
  
  // Upload the replay file
  const filePath = path.join(__dirname, 'fixtures', 'test_replay.json');
  const fileInput = page.locator('#file-input');
  await fileInput.setInputFiles(filePath);
  
  // Wait for the replay to load
  await page.waitForTimeout(2000);
  
  // Check that the card tracker is visible
  await expect(page.locator('#card-tracker')).toBeVisible();
  await expect(page.locator('#card-tracker h3')).toContainText('Cards in deck');
  
  // Check that card counts are displayed
  const cardCounts = page.locator('#card-counts');
  await expect(cardCounts).toBeVisible();
  
  // Take a screenshot of the initial state
  const screenshotDir = path.join(__dirname, '..', 'test-results');
  await page.screenshot({ path: path.join(screenshotDir, 'card-tracker-initial.png'), fullPage: true });
  
  // Step forward a few times
  const stepButton = page.locator('#btn-step-forward');
  await stepButton.click();
  await page.waitForTimeout(1000);
  await stepButton.click();
  await page.waitForTimeout(1000);
  await stepButton.click();
  await page.waitForTimeout(1000);
  
  // Take a screenshot after stepping
  await page.screenshot({ path: path.join(screenshotDir, 'card-tracker-after-steps.png'), fullPage: true });
});
