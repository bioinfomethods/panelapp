import { expect } from "@playwright/test";
import { v4 as uuidv4 } from "uuid";
import { NewReleaseForm } from "../../lib/release";
import { test } from "../../lib/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("primary", async ({ page }) => {
    await page.goto("/releases/");
    await page.getByRole("link", { name: "Create release" }).click();

    const name = uuidv4();
    const form = new NewReleaseForm(page);
    await form.fill({ name, promotionComment: "This is a promotion comment" });
    await form.submit();

    await expect(page.getByRole("heading", { name })).toBeVisible();

    await page.goto("/releases/");

    await page.getByPlaceholder("Search").pressSequentially(name);

    const releaseLink = page.getByRole("link", { name });

    await expect(releaseLink).toBeVisible();

    await releaseLink.click();

    await expect(page.getByRole("heading", { name })).toBeVisible();

    await expect(page.getByText("This is a promotion comment")).toBeVisible();
  });

  test("rename", async ({ page, panels }) => {
    const oldName = uuidv4();
    const newName = uuidv4();

    const id = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: oldName,
    });

    await page.goto(`/releases/${id}/`);

    await page.getByRole("link", { name: "Edit" }).click();

    await page.getByPlaceholder("Name").fill(newName);

    await page.getByRole("button", { name: "Submit" }).click();

    await expect
      .soft(page.getByRole("heading", { name: newName }))
      .toBeVisible();

    await page.goto("/releases/");

    const search = page.getByPlaceholder("Search");

    await search.pressSequentially(newName);
    await expect.soft(page.getByRole("link", { name: newName })).toBeVisible();

    await search.clear();
    await search.pressSequentially(oldName);
    await expect
      .soft(page.getByRole("link", { name: oldName }))
      .not.toBeVisible();
  });
});
