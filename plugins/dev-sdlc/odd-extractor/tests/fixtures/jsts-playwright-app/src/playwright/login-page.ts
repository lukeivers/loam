// SYNTHETIC TEST FIXTURE — Playwright LoginPage page object.
import type { Page } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  async goto(): Promise<void> {
    await this.page.goto('/login');
  }

  async login(email: string, password: string): Promise<void> {
    await this.page.locator('#email').fill(email);
    await this.page.locator('#password').fill(password);
    await this.page.locator('button[type=submit]').click();
  }

  async signUp(email: string, password: string): Promise<void> {
    await this.page.goto('/signup');
    await this.page.locator('#email').fill(email);
    await this.page.locator('#password').fill(password);
  }
}
