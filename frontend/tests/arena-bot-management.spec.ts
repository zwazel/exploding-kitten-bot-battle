import { test, expect } from '@playwright/test';

/**
 * Arena Bot Management UI smoke tests (no backend).
 */

test.describe('Bots - Bot management UI (static)', () => {
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
  
  test('should not throw console errors in arena view', async ({ page }) => {
    const consoleErrors: string[] = [];

    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Navigate to Arena tab
    const arenaTab = page.locator('button[data-view="bots"]');
    await arenaTab.click();
    
    // Wait for a moment to ensure any errors would have fired
    await page.waitForTimeout(500);

    // Check there are no regex-related errors
    expect(consoleErrors.length).toBe(0);
  });

  test('should describe automatic naming in upload card', async ({ page }) => {
    const arenaTab = page.locator('button[data-view="bots"]');
    await arenaTab.click();

    const instructionText = await page.locator('.upload-card .subtle').first().textContent();
    expect(instructionText).toContain('.py');
    expect(instructionText).toContain('Hashes detect');
  });

  test('should restrict uploads to Python files', async ({ page }) => {
    const arenaTab = page.locator('button[data-view="bots"]');
    await arenaTab.click();

    const acceptAttr = await page.locator('#upload-form input[type="file"]').getAttribute('accept');
    expect(acceptAttr).toBe('.py');
  });
});
