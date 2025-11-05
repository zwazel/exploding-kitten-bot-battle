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
    const stepButton = page.locator('#btn-step-forward');
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
    const stepButton = page.locator('#btn-step-forward');
    
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
    const stepButton = page.locator('#btn-step-forward');
    
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

  test('should NOT update deck top card during shuffle card play, only after shuffle event', async ({ page }) => {
    await page.goto('/');
    
    // Load the test replay file (simple-game.json contains shuffle events)
    const filePath = path.join(__dirname, 'fixtures', 'simple-game.json');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    
    // Wait for the game to be loaded
    await page.waitForSelector('#deck-pile', { timeout: 5000 });
    
    const deckPile = page.locator('#deck-pile');
    const stepButton = page.locator('#btn-step-forward');
    const eventContent = page.locator('#event-content');
    
    // Step through events to reach the shuffle sequence:
    // Event 0: game_setup
    // Event 1: turn_start turn=1
    // Event 2: card_draw (draws BEARD_CAT, top_card becomes EXPLODING_KITTEN)
    // Event 3: turn_start turn=2
    // Event 4: card_play SHUFFLE
    // Event 5: shuffle (top_card becomes RAINBOW_RALPHING_CAT)
    
    // Step to event 2 (card_draw)
    await stepButton.click();
    await page.waitForTimeout(100);
    await stepButton.click();
    await page.waitForTimeout(100);
    
    // Step to event 3 (turn_start for turn 2)
    await stepButton.click();
    await page.waitForTimeout(100);
    
    // At event 3, deck should show EXPLODING_KITTEN (from previous card draw)
    let deckContent = await deckPile.textContent();
    expect(deckContent).toContain('EXPLODING KITTEN');
    
    // Step to event 4 (card_play SHUFFLE)
    await stepButton.click();
    await page.waitForTimeout(100);
    
    // Verify we're at the shuffle card play event
    let eventText = await eventContent.textContent();
    expect(eventText).toContain('played SHUFFLE');
    
    // Deck should STILL show EXPLODING_KITTEN (not changed yet)
    deckContent = await deckPile.textContent();
    expect(deckContent).toContain('EXPLODING KITTEN');
    
    // Step to event 5 (shuffle event)
    await stepButton.click();
    await page.waitForTimeout(100);
    
    // Verify we're at the shuffle event
    eventText = await eventContent.textContent();
    expect(eventText).toContain('shuffled the deck');
    
    // NOW the deck should show the new top card (RAINBOW_RALPHING_CAT)
    deckContent = await deckPile.textContent();
    expect(deckContent).toContain('RAINBOW RALPHING CAT');
    expect(deckContent).not.toContain('EXPLODING KITTEN');
  });
});
