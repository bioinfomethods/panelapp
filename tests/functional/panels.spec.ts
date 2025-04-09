import { expect } from "@playwright/test";
import { v4 as uuidv4 } from "uuid";
import { EditPanelForm, NewPanelForm } from "../lib/panel";
import { AddGeneForm } from "../lib/panel-gene";
import { test } from "../lib/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("create", async ({ page }) => {
    await page.goto("/panels/create/");

    const name = uuidv4();
    let form = new NewPanelForm(page);
    await form.fill({
      testId: "1",
      createdBy: "TEST_Curator",
      level4: name,
      description: uuidv4(),
      status: "internal",
    });
    await form.submit();
    await expect(
      page.getByText("Successfully added a new panel")
    ).toBeVisible();

    await page.goto("/panels/");

    await expect(page.locator("#panels_table")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /${name} Version 0\\.0 Internal 0 0%/:
            - cell /${name} Version 0\\.0 Internal/:
              - heading /${name}/ [level=5]:
                - link /${name}/
              - paragraph:
                - text: Version 0.0
                - strong: Internal
            - cell "0 0%"
    `);
  });

  test("add gene", async ({ page, panels }) => {
    const panelName = uuidv4();
    const panelId = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panelName,
      status: "internal",
      description: uuidv4(),
    });

    await page.goto(`/panels/${panelId}/gene/add`);

    let form = new AddGeneForm(page);
    await form.fill({
      testId: "1",
      panelTestId: "1",
      symbol: "BRCA1",
      sources: ["Emory Genetics Laboratory"],
      modeOfInheritance: "MITOCHONDRIAL",
      rating: "Red List (low evidence)",
    });
    await form.submit();

    await expect(page.getByText("Successfully added a new gene")).toBeVisible();

    await page.goto("/panels/entities/BRCA1");

    await expect(page.locator("#table")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row "Red BRCA1 in ${panelName} Version 0.1 Panel not approved review MITOCHONDRIAL Sources Emory Genetics Laboratory":
            - cell "Red BRCA1 in ${panelName} Version 0.1 Panel not approved":
              - heading "Red BRCA1 in ${panelName}" [level=5]:
                - link "BRCA1"
                - link "${panelName}"
              - paragraph: Version 0.1 Panel not approved
            - cell "review"
            - cell "MITOCHONDRIAL"
            - cell "Sources Emory Genetics Laboratory":
              - heading "Sources" [level=6]
              - list:
                - listitem: Emory Genetics Laboratory
    `);

    await page.goto("/panels/");

    await page.getByPlaceholder("Filter panels").pressSequentially(panelName);

    await expect(page.locator("#panels_table")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /${panelName} Version 0\\.1 Internal 1 of 1 \\d+% 1 reviewer   Approve /:
            - cell "${panelName} Version 0.1 Internal":
              - heading "${panelName}" [level=5]:
                - link "${panelName}"
              - paragraph:
                - text: Version 0.1
                - strong: Internal
            - cell /1 of 1 \\d+%/
            - cell "1 reviewer"
            - cell "  Approve ":
              - link ""
              - link " Approve"
              - link ""
    `);
  });

  test("super panels only contain component panel entities", async ({
    page,
    panels,
  }) => {
    const superPanelName = uuidv4();
    const superPanelId = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: superPanelName,
      status: "public",
      description: uuidv4(),
    });
    const childPanelName = uuidv4();
    await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: childPanelName,
      status: "public",
      description: uuidv4(),
    });
    await panels.addPanelGene({
      testId: "1",
      panelTestId: "1",
      symbol: "BRCA1",
      sources: ["Emory Genetics Laboratory"],
      modeOfInheritance: "MITOCHONDRIAL",
      rating: "Red List (low evidence)",
    });
    await panels.addPanelGene({
      testId: "1",
      panelTestId: "2",
      symbol: "BRCA1",
      sources: ["Emory Genetics Laboratory"],
      modeOfInheritance: "BIALLELIC, autosomal or pseudoautosomal",
      rating: "Red List (low evidence)",
    });

    await page.goto(`/panels/${superPanelId}/`);

    await page.getByText("Edit panel").click();
    await expect(page.getByText("Update Information")).toBeVisible();

    const form = new EditPanelForm(page);
    await form.fill({ testId: "1", childPanels: [childPanelName] });
    await form.submit();
    await expect(
      page.getByText("Successfully updated the panel")
    ).toBeVisible();

    await page.goto("/panels/entities/BRCA1");

    await expect(page.locator("#table")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - 'row /Red BRCA1 in ${childPanelName}/':
            - cell "BIALLELIC, autosomal or pseudoautosomal"
    `);

    await expect(page.locator("#table")).not.toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - 'row /Red BRCA1 in ${superPanelName}/':
            - cell "MITOCHONDRIAL"
    `);
  });

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
