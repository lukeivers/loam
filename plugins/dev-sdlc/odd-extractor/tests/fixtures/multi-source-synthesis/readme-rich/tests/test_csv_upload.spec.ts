import { test, expect } from "@playwright/test";

test("csv upload validates rows and rejects malformed entries", async ({ page }) => {
  await page.goto("/upload");
  await page.setInputFiles("input[type=file]", "fixtures/malformed.csv");
  await expect(page.locator(".error-row")).toHaveCount(3);
});
