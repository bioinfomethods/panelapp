import { expect } from "@playwright/test";
import { Then } from ".";

Then("I can navigate to the panels page", async ({ page }) => {
  await page.getByRole("link", { name: "Panels" }).click();

  await expect(
    page.getByRole("heading", { name: /\d+ panels?/ })
  ).toBeVisible();
});

Then("I can navigate to the genes and entities page", async ({ page }) => {
  await page.getByRole("link", { name: "Genes and Entities" }).click();

  await expect(
    page.getByRole("heading", { name: /\d+ genes and genomic entities?/ })
  ).toBeVisible();
});

Then("I can navigate to the activities page", async ({ page }) => {
  await page.getByRole("link", { name: "Activity" }).click();

  await expect(page.getByRole("heading", { name: "Activity" })).toBeVisible();
});

Then("I can navigate to the login page", async ({ page }) => {
  await page.getByRole("link", { name: "Log in" }).click();

  await expect(page.getByRole("heading", { name: "Log in" })).toBeVisible();
});

Then("I can navigate to the account registration page", async ({ page }) => {
  await page.getByRole("link", { name: "Register" }).click();

  await expect(page.getByRole("heading", { name: "Register" })).toBeVisible();
});

Then("I can navigate to the home page", async ({ page }) => {
  await page.getByRole("link", { name: "PanelApp" }).click();

  await expect(
    page.getByRole("heading", { name: "Genomics England PanelApp" })
  ).toBeVisible();
});

Then("I can navigate to the add panel page", async ({ page }) => {
  await page.getByRole("link", { name: "Add panel" }).click();

  await expect(
    page.getByRole("heading", { name: "Panel Creation" })
  ).toBeVisible();
});

Then("I can navigate to the import panel page", async ({ page }) => {
  await page.getByRole("link", { name: "Import panel" }).click();

  await expect(
    page.getByRole("heading", { name: "Import Genes" })
  ).toBeVisible();
});

Then("I cannot navigate to the add panel page", async ({ page }) => {
  await expect(page.getByRole("link", { name: "Add panel" })).not.toBeVisible();
});

Then("I cannot navigate to the import panel page", async ({ page }) => {
  await expect(
    page.getByRole("link", { name: "Import panel" })
  ).not.toBeVisible();
});
