// SYNTHETIC TEST FIXTURE — Playwright DashboardPage page object.
import type { Page } from '@playwright/test';

export class DashboardPage {
  constructor(private page: Page) {}

  async goto(): Promise<void> {
    await this.page.goto('/dashboard');
  }

  async getUserName(): Promise<string> {
    return await this.page.locator('#username').innerText();
  }

  async logout(): Promise<void> {
    await this.page.locator('button#logout').click();
    await this.page.goto('/login');
  }
}
