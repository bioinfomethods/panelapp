import { expect } from "@playwright/test";
import { v4 as uuidv4 } from "uuid";
import { test } from "../lib/test";

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

  test("remove source", async ({ page, panels }) => {
    const panelId = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: uuidv4(),
      description: "Description",
    });

    await panels.addPanelGene({
      panelTestId: "1",
      testId: "1",
      symbol: "BRCA1",
      sources: ["Emory Genetics Laboratory", "UKGTN"],
      modeOfInheritance: "Unknown",
      rating: "Red List (low evidence)",
    });

    await page.goto(`/panels/${panelId}/`);

    await page.getByTestId("unlock-entity-BRCA1").click();

    const source = page
      .getByRole("row", { name: "BRCA1" })
      .getByRole("cell")
      .nth(4)
      .getByText("UKGTN");

    await source.getByRole("link").click();

    await expect(source).not.toBeVisible();
    await expect(
      page
        .getByRole("row", { name: "BRCA1" })
        .getByRole("cell")
        .nth(4)
        .getByText("Emory Genetics Laboratory")
    ).toBeVisible();
  });

  test("remove expert review source", async ({ page, panels }) => {
    const panelId = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: uuidv4(),
      description: "Description",
    });

    await panels.addPanelGene({
      panelTestId: "1",
      testId: "1",
      symbol: "BRCA1",
      sources: ["Emory Genetics Laboratory"],
      modeOfInheritance: "Unknown",
      rating: "Red List (low evidence)",
    });

    await panels.reviewGeneFeedback({
      panelGeneTestId: "1",
      by: "admin",
      rating: { rating: "Amber List (moderate evidence)" },
    });

    await page.goto(`/panels/${panelId}/`);

    await page.getByTestId("unlock-entity-BRCA1").click();

    // Only the one who made the expert review can see this source
    const source = page
      .getByRole("row", { name: "BRCA1" })
      .getByRole("cell")
      .nth(4)
      .getByText("Expert Review Amber");

    await source.getByRole("link").click();

    await expect(source).not.toBeVisible();
    await expect(
      page
        .getByRole("row", { name: "BRCA1" })
        .getByRole("cell")
        .nth(4)
        .getByText("Emory Genetics Laboratory")
    ).toBeVisible();

    await expect(
      page
        .getByRole("row", { name: "BRCA1" })
        .getByRole("cell")
        .nth(0)
        .getByText("Red", { exact: true })
    ).toBeVisible();
  });

  test("add gene: show mop info dialog", async ({ page }) => {
    await page.goto("/panels/1/gene/add");
    await page.getByTestId("add-show-info-mop").click();
    let dialog = page
      .getByRole("dialog")
      .getByText("Mode of pathogenicity Exceptions to loss of function");
    await expect(dialog).toBeVisible();
  });

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
