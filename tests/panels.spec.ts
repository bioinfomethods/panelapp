import { expect, test } from "@playwright/test";
import { CreatePanelPage } from "./pages/create-panel";
import { PanelsPage } from "./pages/panels";

test("panels anonymous", async ({ page }) => {
  await page.goto("/panels");
  await expect(page).toHaveScreenshot("panels-anonymous.png", {
    fullPage: true,
  });
});

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("panels curator", async ({ page }) => {
    await page.goto("/panels");
    await expect(page).toHaveScreenshot("panels-curator.png", {
      fullPage: true,
    });
  });
});

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

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("Super panels only contain component panel entities", async ({
    page,
  }) => {
    const panels = new PanelsPage(page);
    await panels.goto();
    const componentPanel = await panels.findPanel("Test Component Panel 01");
    if (componentPanel !== null) {
      await panels.unlockPanel(componentPanel.id);
      await panels.deletePanel(componentPanel.id);
    }
    const superPanel = await panels.findPanel("Test Super Panel 01");
    if (superPanel !== null) {
      // Page requires refresh to unlock/delete another panel
      await page.reload();
      await panels.unlockPanel(superPanel.id);
      await panels.deletePanel(superPanel.id);
    }
    const createPanel = new CreatePanelPage(page);

    await createPanel.goto();
    const superPanelPage = await createPanel.createPanel({
      level4: "Test Super Panel 01",
      description: "Test super panel",
      childPanels: [],
      status: "public",
    });
    const superPanelAddGene = await superPanelPage.addGene();
    await superPanelAddGene.addGene({
      symbol: "AAAS",
      source: "Other",
      modeOfInheritance: "BIALLELIC, autosomal or pseudoautosomal",
    });

    await createPanel.goto();
    const componentPanelPage = await createPanel.createPanel({
      level4: "Test Component Panel 01",
      description: "Test component panel",
      childPanels: [],
      status: "public",
    });
    const componentPanelAddGene = await componentPanelPage.addGene();
    await componentPanelAddGene.addGene({
      symbol: "AAAS",
      source: "Other",
      modeOfInheritance: "Unknown",
    });

    await superPanelPage.goto();
    const superPanelForm = await superPanelPage.editPanel();
    await superPanelForm.addChildPanel("Test Component Panel 01");
    await superPanelPage.savePanel();

    // Assert

    await superPanelPage.goto();

    await expect(page.getByRole("cell", { name: "Unknown" })).toBeVisible();
    await expect(
      page.getByRole("cell", {
        name: "BIALLELIC, autosomal or pseudoautosomal",
      })
    ).toBeHidden();

    await page.goto("/panels/entities/AAAS");

    await expect(
      page.getByRole("cell", { name: "Red AAAS in Test Component Panel 01" })
    ).toBeVisible();
    await expect(
      page.getByRole("cell", { name: "Red AAAS in Test Super Panel 01" })
    ).toBeHidden();
  });
});
