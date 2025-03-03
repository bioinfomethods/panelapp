import { expect } from "@playwright/test";
import { v4 as uuidv4 } from "uuid";
import { test } from "../../lib/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("update", async ({ page, panels }) => {
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
      promotionComment: "Original comment",
    });

    await page.goto(`/releases/${releaseId}/edit/`);

    await page.getByPlaceholder("Promotion comment").fill("New comment");

    await page.getByRole("button", { name: "Submit" }).click();

    await page.goto(`/releases/${releaseId}/`);

    await expect(page.getByText("New comment")).toBeVisible();
  });

  test("help text", async ({ page, panels }) => {
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
      promotionComment: "Original comment",
    });

    await page.goto(`/releases/${releaseId}/edit/`);

    await expect(
      page.getByText("The comment uses jinja2 template syntax")
    ).toBeVisible();
  });
});
