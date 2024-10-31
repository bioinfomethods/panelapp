import { expect, test } from "@playwright/test";

test("change page", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "News" }).click();

  expect(page.url()).toMatch(/#!News$/);

  await page.getByRole("link", { name: "Reviewers" }).click();

  expect(page.url()).toMatch(/#!Reviewers$/);

  await page.getByRole("link", { name: "Home" }).click();

  expect(page.url()).toMatch(/#!$/);
});
