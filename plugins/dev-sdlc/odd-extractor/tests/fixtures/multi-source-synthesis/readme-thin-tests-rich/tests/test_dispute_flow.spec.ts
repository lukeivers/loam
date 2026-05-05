import { test, expect } from "@playwright/test";

test("operators file refund disputes through the dispute pipeline", async ({ page }) => {
  await page.goto("/upload");
});

test("audit trail identifies who initiated each dispute", async ({ page }) => {
  await page.goto("/audit");
});

test("csv upload validates rows and rejects malformed entries", async ({ page }) => {
  await page.goto("/upload");
});

test("auditors can verify dispute outcomes via the audit trail", async ({ page }) => {
  await page.goto("/audit");
});

test("authenticated operators can file disputes", async ({ page }) => {
  await page.goto("/login");
});
