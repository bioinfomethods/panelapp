import { expect } from "@playwright/test";
import { parse } from "csv/sync";
import { readFileSync } from "fs";
import { v4 as uuidv4 } from "uuid";
import { test } from "../../lib/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("before deployment", async ({ page, panels }) => {
    const panel1Id = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: uuidv4(),
      description: uuidv4(),
      version: "1.0",
      comment: "Panel 1 comment",
    });
    const panel2Id = await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: uuidv4(),
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

    const actual = await exportReleasePanels({ page, releaseId });

    const expected = new Set([
      {
        "Panel ID": panel1Id,
        Promote: "true",
        "Signed Off (Before)": "",
        "Signed Off (After)": "2.0",
        "Comment (Before)": expect.stringMatching("Panel 1 comment"),
        "Comment (After)": expect.stringMatching(
          /Release comment[^]+Panel 1 comment/
        ),
      },
      {
        "Panel ID": panel2Id,
        Promote: "false",
        "Signed Off (Before)": "",
        "Signed Off (After)": "1.0",
        "Comment (Before)": expect.stringMatching("Panel 2 comment"),
        "Comment (After)": expect.stringMatching("Panel 2 comment"),
      },
    ]);

    expect(actual).toEqual(expected);
  });

  test("after deployment", async ({ page, panels }) => {
    const panel1Id = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: uuidv4(),
      description: uuidv4(),
      version: "1.0",
      comment: "Panel 1 comment",
    });
    const panel2Id = await panels.create({
      testId: "2",
      createdBy: "admin",
      level4: uuidv4(),
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

    const actual = await exportReleasePanels({ page, releaseId });

    const expected = new Set([
      {
        "Panel ID": panel1Id,
        Promote: "true",
        "Signed Off (Before)": "",
        "Signed Off (After)": "2.0",
        "Comment (Before)": expect.stringMatching("Panel 1 comment"),
        "Comment (After)": expect.stringMatching(
          /Release comment[^]+Panel 1 comment/
        ),
      },
      {
        "Panel ID": panel2Id,
        Promote: "false",
        "Signed Off (Before)": "",
        "Signed Off (After)": "1.0",
        "Comment (Before)": expect.stringMatching("Panel 2 comment"),
        "Comment (After)": expect.stringMatching("Panel 2 comment"),
      },
    ]);

    expect(actual).toEqual(expected);
  });
});

const exportReleasePanels = async ({ page, releaseId }): Promise<Set<any>> => {
  await page.goto(`/releases/${releaseId}/panels/`);

  const downloadPromise = page.waitForEvent("download");

  await page.getByRole("link", { name: "Export" }).click();

  const download = await downloadPromise;
  const filename = download.suggestedFilename();
  await download.saveAs(filename);

  const rows = parse(readFileSync(filename));

  const actual = new Set(
    rows
      .slice(1)
      .map((cols) => Object.fromEntries(rows[0].map((k, i) => [k, cols[i]])))
  );

  await download.delete();

  return actual;
};
