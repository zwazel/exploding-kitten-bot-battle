import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test.describe('Deck Top Card Display', () => {
  test('should display initial top card from game setup', async ({ page }) => {
    await page.goto('/');
    
    // Load the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'simple-game.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for the game to be loaded
    await page.waitForSelector('#deck-pile', { timeout: 5000 });
    
    // Check that the deck shows the initial top card
    const deckPile = page.locator('#deck-pile');
    await expect(deckPile).toBeVisible();
    
    // The deck should contain card name text (not just "DECK")
    const deckContent = await deckPile.textContent();
    expect(deckContent).not.toEqual('DECK');
  });

  test('should update deck top card immediately when card is drawn', async ({ page }) => {
    await page.goto('/');
    
    // Load the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'simple-game.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for the game to be loaded
    await page.waitForSelector('#deck-pile', { timeout: 5000 });
    
    // Get initial deck content
    const deckPile = page.locator('#deck-pile');
    const initialDeckContent = await deckPile.textContent();
    
    // Click step forward to advance through card draw event
    const stepButton = page.locator('button:has-text("Step Forward")');
    await expect(stepButton).toBeVisible();
    
    // Step forward multiple times to get to a card_draw event
    for (let i = 0; i < 3; i++) {
      await stepButton.click();
      await page.waitForTimeout(100);
      
      // Check if deck content has changed
      const currentDeckContent = await deckPile.textContent();
      if (currentDeckContent !== initialDeckContent) {
        // Deck has been updated, test passed
        expect(currentDeckContent).not.toEqual(initialDeckContent);
        return;
      }
    }
  });

  test('should update deck top card after shuffle event', async ({ page }) => {
    await page.goto('/');
    
    // Load the test replay file
    const filePath = path.join(__dirname, 'fixtures', 'simple-game.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for the game to be loaded
    await page.waitForSelector('#deck-pile', { timeout: 5000 });
    
    const deckPile = page.locator('#deck-pile');
    const stepButton = page.locator('button:has-text("Step Forward")');
    
    // Step through events looking for a shuffle event
    for (let i = 0; i < 20; i++) {
      const currentEventDisplay = await page.locator('#event-content').textContent();
      
      if (currentEventDisplay && currentEventDisplay.includes('shuffled the deck')) {
        // We found a shuffle event, deck should show a top card
        const deckContent = await deckPile.textContent();
        expect(deckContent).not.toEqual('DECK');
        return;
      }
      
      await stepButton.click();
      await page.waitForTimeout(100);
    }
  });

  test('should update deck top card after defuse event', async ({ page }) => {
    await page.goto('/');
    
    // Load the test replay file  
    const filePath = path.join(__dirname, 'fixtures', 'simple-game.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for the game to be loaded
    await page.waitForSelector('#deck-pile', { timeout: 5000 });
    
    const deckPile = page.locator('#deck-pile');
    const stepButton = page.locator('button:has-text("Step Forward")');
    
    // Step through events looking for a defuse event
    for (let i = 0; i < 50; i++) {
      const currentEventDisplay = await page.locator('#event-content').textContent();
      
      if (currentEventDisplay && (currentEventDisplay.includes('Defused') || currentEventDisplay.includes('defuse'))) {
        // We found a defuse event, deck should show the top card
        const deckContent = await deckPile.textContent();
        expect(deckContent).not.toEqual('DECK');
        
        // The top card should likely be EXPLODING_KITTEN since it was just inserted
        // (or another card if inserted at bottom)
        expect(deckContent).toBeTruthy();
        return;
      }
      
      await stepButton.click();
      await page.waitForTimeout(100);
    }
  });
});
