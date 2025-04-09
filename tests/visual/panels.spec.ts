import { expect, test } from "@playwright/test";

test("panels anonymous", async ({ page }) => {
  await page.goto("/panels");
  await expect(page).toHaveScreenshot("panels-anonymous.png", {
    fullPage: true,
  });
});

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("panels curator", async ({ page }) => {
    await page.goto("/panels");
    await expect(page).toHaveScreenshot("panels-curator.png", {
      fullPage: true,
    });
  });
});
