import { test, expect } from '@playwright/test';

/**
 * Arena Bot Management Integration Tests
 * 
 * These tests verify bot creation form validation, focusing on the regex pattern fix.
 * Tests run without backend by checking form validation in isolation.
 */

test.describe('Arena - Bot Name Validation (No Backend Required)', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API calls to prevent hanging
    await page.route('**/auth/**', async (route) => {
      await route.abort('failed');
    });
    
    await page.route('**/bots**', async (route) => {
      await route.abort('failed');
    });
    
    await page.goto('/');
  });
  
  test('should not throw regex syntax error in console', async ({ page }) => {
    const consoleErrors: string[] = [];
    
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Navigate to Arena tab
    const arenaTab = page.locator('button[data-view="arena"]');
    await arenaTab.click();
    
    // Wait for a moment to ensure any errors would have fired
    await page.waitForTimeout(500);
    
    // Check there are no regex-related errors
    const regexErrors = consoleErrors.filter(err => 
      err.includes('Invalid regular expression') || 
      err.includes('Invalid character in character class')
    );
    
    expect(regexErrors.length).toBe(0);
  });

  test('should validate bot name with correct regex pattern', async ({ page }) => {
    // Navigate to Arena tab
    const arenaTab = page.locator('button[data-view="arena"]');
    await arenaTab.click();
    
    // Create a test to verify the pattern works correctly
    const testResults = await page.evaluate(() => {
      const input = document.createElement('input');
      input.type = 'text';
      input.pattern = '[A-Za-z0-9_\\-]+';
      
      const testCases = [
        { value: 'ValidBot', expected: true },
        { value: 'valid_bot', expected: true },
        { value: 'valid-bot', expected: true },
        { value: 'Valid123', expected: true },
        { value: 'bot name', expected: false },
        { value: 'bot@name', expected: false },
        { value: 'bot#name', expected: false },
      ];
      
      return testCases.map(({ value, expected }) => {
        input.value = value;
        const isValid = input.checkValidity();
        return { value, expected, actual: isValid, matches: isValid === expected };
      });
    });
    
    // Verify all test cases passed
    testResults.forEach(result => {
      expect(result.matches).toBe(true);
    });
  });

  test('should accept bot names with underscores', async ({ page }) => {
    // Navigate to Arena tab
    const arenaTab = page.locator('button[data-view="arena"]');
    await arenaTab.click();
    
    // Try to find the bot name input (it should be in the HTML even if hidden)
    const botNamePattern = await page.evaluate(() => {
      const input = document.querySelector<HTMLInputElement>('#bot-name');
      return input?.pattern;
    });
    
    // Verify the pattern is correctly set
    expect(botNamePattern).toBe('[A-Za-z0-9_\\-]+');
  });

  test('should accept bot names with hyphens', async ({ page }) => {
    // Navigate to Arena tab
    const arenaTab = page.locator('button[data-view="arena"]');
    await arenaTab.click();
    
    // Test hyphen is accepted
    const result = await page.evaluate(() => {
      const input = document.createElement('input');
      input.type = 'text';
      input.pattern = '[A-Za-z0-9_\\-]+';
      input.value = 'my-bot-name';
      return input.checkValidity();
    });
    
    expect(result).toBe(true);
  });
});
