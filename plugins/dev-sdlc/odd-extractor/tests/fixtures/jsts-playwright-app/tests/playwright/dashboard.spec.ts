// SYNTHETIC TEST FIXTURE — Playwright dashboard spec.
import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../src/playwright/dashboard-page';

test.describe('dashboard view', () => {
  test('shows the username when logged in', async ({ page }) => {
    const dash = new DashboardPage(page);
    await dash.goto();
    const name = await dash.getUserName();
    expect(name).toContain('alice');
  });

  test('logout returns to login page', async ({ page }) => {
    const dash = new DashboardPage(page);
    await dash.goto();
    await dash.logout();
    await expect(page).toHaveURL(/login/);
  });
});
