import { expect } from "@playwright/test";
import { test } from "../lib/test";

test("navigate to panels page", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "Panels" }).click();

  await expect(
    page.getByRole("heading", { name: /\d+ panels?/ })
  ).toBeVisible();
});

test("navigate to genes and entities page", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "Genes and Entities" }).click();

  await expect(
    page.getByRole("heading", { name: /\d+ genes and genomic entities?/ })
  ).toBeVisible();
});

test("navigate to activities page", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "Activity" }).click();

  await expect(page.getByRole("heading", { name: "Activity" })).toBeVisible();
});

test("navigate to login page", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "Log in" }).click();

  await expect(page.getByRole("heading", { name: "Log in" })).toBeVisible();
});

test("navigate to registration page", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "Register" }).click();

  await expect(page.getByRole("heading", { name: "Register" })).toBeVisible();
});

test("navigate to home page", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "PanelApp" }).click();

  await expect(
    page.getByRole("heading", { name: "Genomics England PanelApp" })
  ).toBeVisible();
});

test("cannot navigate to add panel page", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("link", { name: "Add panel" })).not.toBeVisible();
});

test("cannot navigate to import panel page", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("link", { name: "Import panel" })
  ).not.toBeVisible();
});

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("navigate to add panel page", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("link", { name: "Add panel" }).click();

    await expect(
      page.getByRole("heading", { name: "Panel Creation" })
    ).toBeVisible();
  });

  test("navigate to import panel page", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("link", { name: "Import panel" }).click();

    await expect(
      page.getByRole("heading", { name: "Import Genes" })
    ).toBeVisible();
  });
});
