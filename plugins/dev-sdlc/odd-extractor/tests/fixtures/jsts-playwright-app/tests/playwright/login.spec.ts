// SYNTHETIC TEST FIXTURE — Playwright login spec.
import { test, expect } from '@playwright/test';
import { LoginPage } from '../../src/playwright/login-page';

test.describe('login flow', () => {
  test('user can log in with valid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('alice@example.com', 'correct-password');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('rejects an empty password', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('alice@example.com', '');
    await expect(page.locator('.error')).toBeVisible();
  });

  test('rejects an invalid email format', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('not-an-email', 'whatever');
    await expect(page.locator('.error')).toBeVisible();
  });
});
