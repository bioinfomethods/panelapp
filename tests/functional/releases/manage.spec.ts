import { expect } from "@playwright/test";
import { v4 as uuidv4 } from "uuid";
import { ReleaseListPage } from "../../lib/release";
import { ReleasePanelListPage } from "../../lib/release-panel";
import { test } from "../../lib/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("release panel summary", async ({ page, panels }) => {
    await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: uuidv4(),
      description: uuidv4(),
    });
    await panels.create({
      testId: "2",
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
      { testId: "2", panelTestId: "2", releaseTestId: "1", promote: false },
    ]);

    await page.goto(`/releases/${releaseId}/`);

    await expect(page.locator("#summary")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row "Change Count":
            - cell "Change"
            - cell "Count"
        - rowgroup:
          - row "Sign Off 2":
            - cell "Sign Off"
            - cell "2"
          - row "Promote 1":
            - cell "Promote"
            - cell "1"
    `);
  });

  test("release panels", async ({ page, panels }) => {
    const panel1Name = uuidv4();
    await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panel1Name,
      description: uuidv4(),
      version: "0.0",
    });
    const panel2Name = uuidv4();
    await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: panel2Name,
      description: uuidv4(),
      version: "0.0",
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    await panels.setReleasePanels([
      { testId: "1", panelTestId: "1", releaseTestId: "1", promote: true },
      { testId: "2", panelTestId: "2", releaseTestId: "1", promote: false },
    ]);

    await page.goto(`/releases/${releaseId}/panels/`);

    await expect(page.locator("#panels")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row "ID Name  Status Changes Signed Off (Before) Signed Off (After)":
            - cell "ID"
            - cell "Name "
            - cell "Status"
            - cell "Changes"
            - cell "Signed Off (Before)"
            - cell "Signed Off (After)"
    `);
    await expect(page.locator("#panels")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /\\d+ ${panel1Name} internal  Promote  Sign Off 1\\.0/:
            - cell /\\d+/
            - cell "${panel1Name}":
              - heading "${panel1Name}" [level=5]:
                - link "${panel1Name}"
            - cell "internal"
            - cell " Promote  Sign Off":
              - list:
                - listitem:  Promote
                - listitem:  Sign Off
            - cell
            - cell "1.0"
    `);
    await expect(page.locator("#panels")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /\\d+ ${panel2Name} internal  Sign Off 0\\.0/:
            - cell /\\d+/
            - cell "${panel2Name}":
              - heading "${panel2Name}" [level=5]:
                - link "${panel2Name}"
            - cell "internal"
            - cell " Sign Off":
              - list:
                - listitem:  Sign Off
            - cell
            - cell "0.0"
    `);
  });

  test("filter releases by name", async ({ page, panels }) => {
    const release1Name = uuidv4();
    await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: release1Name,
    });
    const release2Name = uuidv4();
    await panels.createRelease({
      testId: "2",
      createdBy: "admin",
      name: release2Name,
    });

    const listPage = new ReleaseListPage(page);
    await listPage.goto();

    await listPage.find({
      search: release1Name,
    });

    await expect(page.locator("#releases")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /${release1Name} PENDING 0/:
            - cell "${release1Name}":
              - link "${release1Name}"
            - cell "PENDING"
            - cell "0"
    `);
  });

  test("filter panels by name", async ({ page, panels }) => {
    const panel1Name = uuidv4();
    await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panel1Name,
      description: uuidv4(),
      version: "0.0",
    });
    const panel2Name = uuidv4();
    await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: panel2Name,
      description: uuidv4(),
      version: "0.0",
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    await panels.setReleasePanels([
      { testId: "1", panelTestId: "1", releaseTestId: "1", promote: true },
      { testId: "2", panelTestId: "2", releaseTestId: "1", promote: false },
    ]);

    const listPage = new ReleasePanelListPage(page, releaseId);
    await listPage.goto();

    await listPage.find({
      search: panel1Name,
    });

    await expect(page.locator("#panels")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /\\d+ ${panel1Name}/
    `);
    await expect(page.locator("#panels")).not.toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /\\d+ ${panel2Name}/
    `);
  });

  test("filter panels by status", async ({ page, panels }) => {
    const panel1Name = uuidv4();
    await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panel1Name,
      description: uuidv4(),
      version: "0.0",
      status: "public",
    });
    const panel2Name = uuidv4();
    await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: panel2Name,
      description: uuidv4(),
      version: "0.0",
      status: "internal",
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    await panels.setReleasePanels([
      { testId: "1", panelTestId: "1", releaseTestId: "1", promote: true },
      { testId: "2", panelTestId: "2", releaseTestId: "1", promote: false },
    ]);

    const listPage = new ReleasePanelListPage(page, releaseId);
    await listPage.goto();

    await listPage.find({ statuses: ["public"] });
    await expect(page.locator("#panels")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /\\d+ ${panel1Name}/
    `);
    await expect(page.locator("#panels")).not.toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /\\d+ ${panel2Name}/
    `);
  });

  test("filter panels by types", async ({ page, panels }) => {
    const panel1Name = uuidv4();
    await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panel1Name,
      description: uuidv4(),
      version: "0.0",
      panelTypes: ["Rare Disease 100K"],
    });
    const panel2Name = uuidv4();
    await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: panel2Name,
      description: uuidv4(),
      version: "0.0",
      panelTypes: ["Rare Disease Test Directory", "Reference"],
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
    });

    await panels.setReleasePanels([
      { testId: "1", panelTestId: "1", releaseTestId: "1", promote: true },
      { testId: "2", panelTestId: "2", releaseTestId: "1", promote: false },
    ]);

    const listPage = new ReleasePanelListPage(page, releaseId);
    await listPage.goto();

    await listPage.find({
      types: ["Rare Disease Test Directory", "Reference"],
    });
    await expect(page.locator("#panels")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /\\d+ ${panel2Name}/
    `);
    await expect(page.locator("#panels")).not.toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /\\d+ ${panel1Name}/
    `);
  });
});
