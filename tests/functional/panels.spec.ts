import { expect, test } from "@playwright/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("lock/unlock entity", async ({ page }) => {
    await page.goto("/panels/2/");
    page.once("dialog", (dialog) => {
      dialog.dismiss().catch(() => {});
    });

    await page.getByTestId("unlock-entity-AAAS").click();

    await expect(page.getByTestId("unlock-entity-AAAS")).toBeHidden();
    await expect(page.getByTestId("lock-entity-AAAS")).toBeVisible();
    await expect(page.getByTestId("delete-entity-AAAS")).toBeVisible();

    await page.getByTestId("lock-entity-AAAS").click();

    await expect(page.getByTestId("unlock-entity-AAAS")).toBeVisible();
    await expect(page.getByTestId("lock-entity-AAAS")).toBeHidden();
    await expect(page.getByTestId("delete-entity-AAAS")).toBeHidden();
  });
});

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("add gene: show mop info dialog", async ({ page }) => {
    await page.goto("/panels/1/gene/add");
    await page.getByTestId("add-show-info-mop").click();
    let dialog = page
      .getByRole("dialog")
      .getByText("Mode of pathogenicity Exceptions to loss of function");
    await expect(dialog).toBeVisible();
  });
});

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("review gene: show rating info dialog", async ({ page }) => {
    await page.goto("/panels/2/gene/AAAS/");
    await page.getByTestId("review-show-info-rating").click();
    let dialog = page
      .getByRole("dialog")
      .getByText(
        "Rating If promoting or demoting a gene, please provide comments to justify a dec"
      );
    await expect(dialog).toBeVisible();
  });
});

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("edit gene: show mode of pathogenicity info dialog", async ({
    page,
  }) => {
    await page.goto("/panels/2/gene/AAAS/#!details");
    await page.getByRole("link").filter({ hasText: "Edit gene" }).click();
    await page.getByTestId("details-show-info-mop").click();
    let dialog = page
      .getByRole("dialog")
      .getByText(
        "Mode of pathogenicity Exceptions to loss of function It’s assumed that loss-of-"
      );
    await expect(dialog).toBeVisible();
  });
});
