import { expect } from "@playwright/test";
import { v4 as uuidv4 } from "uuid";
import { test } from "../../lib/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("primary", async ({ page, panels }) => {
    const panel1Name = uuidv4();
    await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panel1Name,
      description: uuidv4(),
      version: "1.0",
      comment: "Panel 1 comment",
    });
    const panel2Name = uuidv4();
    await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: panel2Name,
      description: uuidv4(),
      version: "1.0",
      comment: "Panel 2 comment",
    });
    const releaseId = await panels.createRelease({
      testId: "1",
      createdBy: "admin",
      name: uuidv4(),
      promotionComment: "Release comment",
    });
    await panels.setReleasePanels([
      { testId: "1", releaseTestId: "1", panelTestId: "1", promote: true },
      { testId: "2", releaseTestId: "1", panelTestId: "2", promote: false },
    ]);

    await page.goto(`/releases/${releaseId}/deployment/`);

    page.on("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Deploy" }).click();

    await expect(page.getByText("DONE")).toBeVisible({ timeout: 15000 });

    await page.goto("/panels/activity/");
    const search = page.getByPlaceholder("Filter activities");

    await search.pressSequentially(panel1Name);
    await expect(page.getByRole("table")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /${panel1Name} v2\\.1 Curator Test Panel version 2\\.0 has been signed off on \\d+-\\d+-\\d+/
          - row /${panel1Name} v2\\.0 Curator Test promoted panel to version 2\\.0/
    `);

    await search.clear();
    await search.pressSequentially(panel2Name);
    await expect(page.getByRole("table")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /${panel2Name} v1\\.1 Curator Test Panel version 1\\.0 has been signed off on \\d+-\\d+-\\d+/
    `);
  });
});
