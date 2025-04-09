import AxeBuilder from "@axe-core/playwright";
import { expect } from "@playwright/test";
import { test } from "../lib/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("releases", async ({ page }) => {
    await page.goto("/releases/");

    const results = await new AxeBuilder({ page }).analyze();

    expect(results.violations).toEqual([]);
  });
});
