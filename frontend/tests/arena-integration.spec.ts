import { test, expect } from '@playwright/test';

/**
 * Arena Authentication and Bot Management Integration Tests
 * 
 * These tests verify the full authentication and bot management flow
 * with a mocked backend API.
 */

// Mock data
const mockUser = {
  id: 1,
  username: 'testuser',
  display_name: 'Test User',
  email: 'test@example.com',
  is_admin: false,
};

const mockToken = { access_token: 'mock-jwt-token-12345' };

const mockBots = [
  {
    id: 1,
    name: 'TestBot1',
    label: 'testuser_testbot1',
    created_at: '2025-01-01T00:00:00Z',
    versions_count: 2,
    latest_version: 2,
  },
];

test.describe('Arena - Full Integration Tests', () => {
  test('should complete full bot creation flow with mocked backend', async ({ page }) => {
    let botsCreated = 0;
    
    // Mock authentication endpoints
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({ json: mockToken });
    });

    await page.route('**/auth/me', async (route) => {
      await route.fulfill({ json: mockUser });
    });

    // Mock bots endpoint
    await page.route('**/bots', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: mockBots });
      } else if (route.request().method() === 'POST') {
        botsCreated++;
        const body = JSON.parse(await route.request().postData() || '{}');
        const newBot = {
          id: 2 + botsCreated,
          name: body.name,
          label: `testuser_${body.name.toLowerCase()}`,
          created_at: new Date().toISOString(),
          versions_count: 0,
          latest_version: 0,
        };
        await route.fulfill({ json: newBot, status: 201 });
      }
    });

    // Go to page
    await page.goto('/');
    
    // Navigate to Arena tab
    await page.locator('button[data-view="arena"]').click();
    
    // Wait for login form to be visible
    await expect(page.locator('#login-form')).toBeVisible();
    
    // Fill in login credentials
    await page.locator('#login-form input[name="email"]').fill('test@example.com');
    await page.locator('#login-form input[name="password"]').fill('password123');
    
    // Submit login form
    await page.locator('#login-form button[type="submit"]').click();
    
    // Wait for dashboard to be visible
    await expect(page.locator('.arena-dashboard')).toBeVisible({ timeout: 5000 });
    
    // Verify user info is displayed
    await expect(page.locator('#arena-user-info')).toContainText('Test User');
    
    // Fill in bot creation form
    const botNameInput = page.locator('#bot-name');
    await botNameInput.fill('MyTestBot');
    
    // Verify the input is valid
    const isValid = await botNameInput.evaluate((el: HTMLInputElement) => el.validity.valid);
    expect(isValid).toBe(true);
    
    // Submit bot creation form
    await page.locator('#create-bot-form button[type="submit"]').click();
    
    // Wait a moment for the bot to be created
    await page.waitForTimeout(500);
    
    // Verify a bot was created via API
    expect(botsCreated).toBe(1);
  });

  test('should prevent invalid bot names from being submitted', async ({ page }) => {
    // Mock authentication endpoints
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({ json: mockToken });
    });

    await page.route('**/auth/me', async (route) => {
      await route.fulfill({ json: mockUser });
    });

    await page.route('**/bots', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: mockBots });
      }
    });

    // Go to page
    await page.goto('/');
    
    // Navigate to Arena tab
    await page.locator('button[data-view="arena"]').click();
    
    // Login
    await page.locator('#login-form input[name="email"]').fill('test@example.com');
    await page.locator('#login-form input[name="password"]').fill('password123');
    await page.locator('#login-form button[type="submit"]').click();
    
    // Wait for dashboard
    await expect(page.locator('.arena-dashboard')).toBeVisible({ timeout: 5000 });
    
    // Try to create a bot with invalid name (spaces)
    const botNameInput = page.locator('#bot-name');
    await botNameInput.fill('Invalid Bot Name');
    
    // Verify the input is invalid
    const isValid = await botNameInput.evaluate((el: HTMLInputElement) => el.validity.valid);
    expect(isValid).toBe(false);
    
    // Try to submit (should be prevented by HTML5 validation)
    const createButton = page.locator('#create-bot-form button[type="submit"]');
    await createButton.click();
    
    // Check that the validation message appears
    const validationMessage = await botNameInput.evaluate((el: HTMLInputElement) => el.validationMessage);
    expect(validationMessage).not.toBe('');
  });

  test('should show logout button when logged in', async ({ page }) => {
    // Mock authentication endpoints
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({ json: mockToken });
    });

    await page.route('**/auth/me', async (route) => {
      await route.fulfill({ json: mockUser });
    });

    await page.route('**/bots', async (route) => {
      await route.fulfill({ json: mockBots });
    });

    // Go to page
    await page.goto('/');
    
    // Navigate to Arena tab
    await page.locator('button[data-view="arena"]').click();
    
    // Login
    await page.locator('#login-form input[name="email"]').fill('test@example.com');
    await page.locator('#login-form input[name="password"]').fill('password123');
    await page.locator('#login-form button[type="submit"]').click();
    
    // Wait for dashboard
    await expect(page.locator('.arena-dashboard')).toBeVisible({ timeout: 5000 });
    
    // Check logout button is visible
    const logoutButton = page.locator('#logout-button');
    await expect(logoutButton).toBeVisible();
    await expect(logoutButton).toContainText('Log out');
  });
});
