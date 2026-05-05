import { test, expect } from "@playwright/test";

test("auditors can verify dispute outcomes via the audit trail", async ({ page }) => {
  await page.goto("/audit");
  await page.click(".case-1234");
  await expect(page.locator(".outcome")).toBeVisible();
});
