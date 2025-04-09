import { Page, test as setup } from "@playwright/test";
import { LoginPage } from "../lib/login";

const authenticate = async (page: Page, username: string, password: string) => {
  const login = new LoginPage(page);
  await login.goto();
  await login.login(username, password);

  await page
    .context()
    .storageState({ path: `playwright/.auth/${username}.json` });
};

setup("authenticate as admin", async ({ page }) => {
  await authenticate(page, "admin", "changeme");
});

setup("authenticate as TEST_Curator", async ({ page }) => {
  await authenticate(page, "TEST_Curator", "changeme");
});

setup("authenticate as TEST_Reviewer", async ({ page }) => {
  await authenticate(page, "TEST_Reviewer", "changeme");
});
