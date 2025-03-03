import { expect, Page } from "@playwright/test";
import { stringify } from "csv/sync";
import { v4 as uuidv4 } from "uuid";
import { ImportReleasePanelsPage } from "../../lib/release-panel";
import { test } from "../../lib/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("primary", async ({ page, panels }) => {
    const panel1Name = uuidv4();
    const panel1Id = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panel1Name,
      description: uuidv4(),
    });
    const panel2Name = uuidv4();
    const panel2Id = await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: panel2Name,
      description: uuidv4(),
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    const rows = [
      ["Panel ID", "Promote"],
      [panel1Id, "true"],
      [panel2Id, "false"],
    ];

    await importReleasePanels({ page, releaseId, rows });

    await expectReleasePanel({
      page,
      releaseId,
      panel: { id: panel1Id, level4: panel1Name },
      promote: true,
    });
    await expectReleasePanel({
      page,
      releaseId,
      panel: { id: panel2Id, level4: panel2Name },
      promote: false,
    });
  });

  test("source of truth", async ({ page, panels }) => {
    const panel1Name = uuidv4();
    await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panel1Name,
      description: uuidv4(),
    });
    const panel2Name = uuidv4();
    const panel2Id = await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: panel2Name,
      description: uuidv4(),
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });
    await panels.setReleasePanels([
      { testId: "1", panelTestId: "1", releaseTestId: "1", promote: true },
    ]);

    const rows = [
      ["Panel ID", "Promote"],
      [panel2Id, "false"],
    ];

    await importReleasePanels({ page, releaseId, rows });

    await expectReleasePanel({
      page,
      releaseId,
      panel: { id: panel2Id, level4: panel2Name },
      promote: false,
    });

    await page.goto(`/releases/${releaseId}/panels/`);
    await page.getByPlaceholder("Search").pressSequentially(panel1Name);
    await expect(page.getByRole("row", { name: panel1Name })).not.toBeVisible();
  });

  test("help text", async ({ page, panels }) => {
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    const importPage = new ImportReleasePanelsPage(page, releaseId);
    await importPage.goto();

    await page.getByRole("link", { name: "" }).click();

    await expect(
      page.getByText(
        "File Format Requirements The import file must be in CSV format"
      )
    ).toBeVisible();
  });

  test("on error no import", async ({ page, panels }) => {
    const panelName = uuidv4();
    const panelId = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panelName,
      description: uuidv4(),
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    const rows = [
      ["Panel ID", "Promote"],
      [panelId, "wrong"],
    ];

    await importReleasePanels({ page, releaseId, rows });

    await page.goto(`/releases/${releaseId}/panels/`);
    await page.getByPlaceholder("Search").pressSequentially(panelName);
    await expect(page.getByRole("row", { name: panelName })).not.toBeVisible();
  });

  test("invalid fields", async ({ page, panels }) => {
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    const rows = [
      ["invalid", "header"],
      ["1", "true"],
      ["2", "false"],
    ];

    await importReleasePanels({ page, releaseId, rows });

    await expect
      .soft(page.getByText("Missing headers: `Panel ID`, `Promote`"))
      .toBeVisible();

    await expect
      .soft(page.getByText("Row 1: Panel ID: This field cannot be null."))
      .toBeVisible();

    await expect
      .soft(
        page.getByText(
          "Row 1: Promote: “None” value must be either True or False."
        )
      )
      .toBeVisible();

    await expect
      .soft(page.getByText("Row 2: Panel ID: This field cannot be null."))
      .toBeVisible();

    await expect
      .soft(
        page.getByText(
          "Row 2: Promote: “None” value must be either True or False."
        )
      )
      .toBeVisible();
  });

  test("invalid panel id", async ({ page, panels }) => {
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    const rows = [
      ["Panel ID", "Promote"],
      ["one", "true"],
    ];

    await importReleasePanels({ page, releaseId, rows });

    await expect
      .soft(
        page.getByText(
          "Row 1: Field 'Panel ID' expected a number but got 'one'."
        )
      )
      .toBeVisible();
  });

  test("missing panel", async ({ page, panels }) => {
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    const rows = [
      ["Panel ID", "Promote"],
      ["0", "true"],
    ];

    await importReleasePanels({ page, releaseId, rows });

    await expect
      .soft(page.getByText("Row 1: Panel does not exist"))
      .toBeVisible();
  });

  test("invalid promote", async ({ page, panels }) => {
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    const rows = [
      ["Panel ID", "Promote"],
      ["1", "yes"],
    ];

    await importReleasePanels({ page, releaseId, rows });

    await expect
      .soft(
        page.getByText(
          "Row 1: Promote: `yes` value must be either `true` or `false`."
        )
      )
      .toBeVisible();
  });

  test("duplicate panels", async ({ page, panels }) => {
    await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: uuidv4(),
      description: uuidv4(),
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    const rows = [
      ["Panel ID", "Promote"],
      ["1", "true"],
      ["1", "false"],
    ];

    await importReleasePanels({ page, releaseId, rows });

    await expect
      .soft(page.getByText("Row 2: Panel is a duplicate"))
      .toBeVisible();
  });

  test("after deployment", async ({ page, panels }) => {
    await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: uuidv4(),
      description: uuidv4(),
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });
    await panels.setReleasePanels([
      { testId: "1", panelTestId: "1", releaseTestId: "1", promote: true },
    ]);

    await panels.deployRelease("1");

    await page.goto(`/releases/${releaseId}/panels/`);

    await expect(page.getByRole("link", { name: " Import" })).toBeDisabled();
  });
});

const importReleasePanels = async ({
  page,
  releaseId,
  rows,
}: {
  page: Page;
  releaseId: string;
  rows: string[][];
}) => {
  const encoded = stringify(rows);

  const importPage = new ImportReleasePanelsPage(page, releaseId);
  await importPage.goto();
  await importPage.importFromCsv(encoded);
};

const expectReleasePanel = async ({
  page,
  releaseId,
  panel,
  promote,
  signedOffBefore,
  signedOffAfter,
}: {
  page: Page;
  releaseId: string;
  panel: { id: string; level4: string };
  promote: boolean;
  signedOffBefore?: string;
  signedOffAfter?: string;
}) => {
  await page.goto(`/releases/${releaseId}/panels/`);

  await page.getByPlaceholder("Search").pressSequentially(panel.level4);

  const panelRow = page.getByRole("row", { name: panel.level4 });

  await expect.soft(panelRow).toBeVisible();

  await expect.soft(panelRow.getByRole("cell").nth(0)).toHaveText(panel.id);

  await expect
    .soft(panelRow.getByRole("listitem").filter({ hasText: "Sign Off" }))
    .toBeVisible();

  if (promote) {
    await expect
      .soft(panelRow.getByRole("listitem").filter({ hasText: "Promote" }))
      .toBeVisible();
  } else {
    await expect
      .soft(panelRow.getByRole("listitem").filter({ hasText: "Promote" }))
      .not.toBeVisible();
  }

  if (signedOffBefore) {
    await expect
      .soft(panelRow.getByRole("cell").nth(3))
      .toContainText(signedOffBefore);
  }

  if (signedOffAfter) {
    await expect
      .soft(panelRow.getByRole("cell").nth(4))
      .toContainText(signedOffAfter);
  }
};
