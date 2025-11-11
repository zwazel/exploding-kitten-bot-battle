import { test, expect } from '@playwright/test';
import { Buffer } from 'buffer';

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
    name: 'testbot',
    qualified_name: 'testuser_testbot',
    created_at: '2025-01-01T00:00:00Z',
    current_version: {
      id: 10,
      version_number: 1,
      created_at: '2025-01-01T01:00:00Z',
      is_active: true,
      file_hash: 'abc12345',
    },
  },
];

const mockProfiles: Record<number, unknown> = {
  1: {
    id: 1,
    name: 'testbot',
    qualified_name: 'testuser_testbot',
    created_at: '2025-01-01T00:00:00Z',
    current_version: {
      id: 10,
      version_number: 1,
      created_at: '2025-01-01T01:00:00Z',
      is_active: true,
      file_hash: 'abc12345',
    },
    versions: [
      {
        id: 10,
        version_number: 1,
        created_at: '2025-01-01T01:00:00Z',
        is_active: true,
        file_hash: 'abc12345',
      },
    ],
    recent_replays: [],
  },
};

test.describe('Arena - Full Integration Tests', () => {
  test('should complete bot upload flow with mocked backend', async ({ page }) => {
    let uploadCount = 0;
    let bots = [...mockBots];

    // Mock authentication endpoints
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({ json: mockToken });
    });

    await page.route('**/auth/me', async (route) => {
      await route.fulfill({ json: mockUser });
    });

    await page.route('**/bots', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: bots });
      }
    });

    await page.route('**/bots/*', async (route) => {
      if (route.request().method() === 'GET') {
        const url = new URL(route.request().url());
        const id = Number.parseInt(url.pathname.split('/').pop() ?? '', 10);
        const profile = mockProfiles[id];
        await route.fulfill({ json: profile ?? mockProfiles[1] });
      }
    });

    await page.route('**/bots/upload', async (route) => {
      uploadCount++;
      const headers = route.request().headers();
      expect(headers['content-type']).toContain('multipart/form-data');

      const newBotId = 100 + uploadCount;
      const botSummary = {
        id: newBotId,
        name: 'uploadbot',
        qualified_name: 'testuser_uploadbot',
        created_at: new Date().toISOString(),
        current_version: {
          id: 900 + uploadCount,
          version_number: 1,
          created_at: new Date().toISOString(),
          is_active: true,
          file_hash: 'feedbeef',
        },
      };
      bots = [botSummary, ...mockBots];
      mockProfiles[newBotId] = {
        ...botSummary,
        versions: [botSummary.current_version],
        recent_replays: [],
      };

      await route.fulfill({
        json: {
          status: 'created',
          bot: botSummary,
          version: botSummary.current_version,
        },
      });
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

    // Upload a bot file
    await page.setInputFiles('#bot-file', {
      name: 'UploadBot.py',
      mimeType: 'text/x-python',
      buffer: Buffer.from('class Bot: pass'),
    });

    await page.locator('#upload-form button[type="submit"]').click();

    await expect(page.locator('#upload-feedback')).toContainText('Created bot');
    expect(uploadCount).toBe(1);
  });

  test('should enable arena match controls after login', async ({ page }) => {
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

    await page.route('**/bots/1', async (route) => {
      await route.fulfill({ json: mockProfiles[1] });
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

    // Switch back to viewer to inspect embedded arena controls
    await page.locator('button[data-view="viewer"]').click();

    // Arena controls should be visible with a start button
    await expect(page.locator('#arena-controls')).toBeVisible();
    await expect(page.locator('#arena-start')).toBeEnabled();
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

    await page.route('**/bots/1', async (route) => {
      await route.fulfill({ json: mockProfiles[1] });
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
