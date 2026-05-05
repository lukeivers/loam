import { test, expect } from "@playwright/test";

test("operators file refund disputes through the dispute pipeline", async ({ page }) => {
  await page.goto("/upload");
  await page.setInputFiles("input[type=file]", "fixtures/disputes.csv");
  await page.click("button[type=submit]");
  await expect(page.locator(".outcome-row")).toHaveCount(10);
});

test("audit trail identifies who initiated each dispute", async ({ page }) => {
  await page.goto("/audit");
  await expect(page.locator(".audit-row")).toContainText("operator-1");
});
