import { test as setup, expect } from "@playwright/test";

const authFile = "playwright/.auth/admin.json";

setup("authenticate", async ({ page }) => {
  await page.goto("/accounts/login/?next=/");
  await page.getByPlaceholder("Username").click();
  await page.getByPlaceholder("Username").fill("admin");
  await page.getByPlaceholder("Password").click();
  await page.getByPlaceholder("Password").fill("changeme");
  await page.getByRole("button", { name: "Log in" }).click();
  // Wait until the page reaches a state where all cookies are set.
  await expect(page.getByRole("link", { name: "Log out" })).toBeVisible();

  await page.context().storageState({ path: authFile });
});
