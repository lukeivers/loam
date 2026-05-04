// SYNTHETIC TEST FIXTURE — Playwright configuration.
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/playwright',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:3000',
  },
  reporter: 'list',
});
