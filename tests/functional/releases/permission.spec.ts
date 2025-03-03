import { expect } from "@playwright/test";
import { test } from "../../lib/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("privileged users can manage releases", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("link", { name: "Releases" })).toBeVisible();

    await page.goto("/releases/");

    await expect(page.getByRole("heading", { name: "Releases" })).toBeVisible();
  });
});

test("unprivileged users cannot manage releases", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("link", { name: "Releases" })).not.toBeVisible();

  await page.goto("/releases/");

  await expect(
    page.getByRole("heading", { name: "Releases" })
  ).not.toBeVisible();
});
