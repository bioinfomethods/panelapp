import { expect, test } from "@playwright/test";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("home", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveScreenshot("home.png");
  });
});

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("panel detail curator", async ({ page }) => {
    await page.goto("/panels/2/");
    await expect(page).toHaveScreenshot("panel-detail-curator.png", {
      fullPage: true,
    });
  });
});

test("panel gene review", async ({ page }) => {
  await page.goto("/panels/2/gene/BRCA1/");
  let review = page.getByText(
    "(Other) Green List (high evidence) TestingOverSeveralLinesSources: Radboud Unive"
  );
  await expect(review).toHaveScreenshot("panel-gene-review.png");
});

test("genes and entities list", async ({ page }) => {
  await page.goto("/panels/entities/");
  await expect(page).toHaveScreenshot("genes-and-entities-list.png", {
    fullPage: true,
  });
});

test("compare panels", async ({ page }) => {
  await page.goto("/panels/compare/1/2");
  await expect(page).toHaveScreenshot("compare-panels.png", { fullPage: true });
});

test("login", async ({ page }) => {
  await page.goto("/accounts/login/");
  await expect(page).toHaveScreenshot("login.png", { fullPage: true });
});

test("entity detail", async ({ page }) => {
  await page.goto("/panels/entities/BRCA1");
  await expect(page).toHaveScreenshot("entity-detail.png", { fullPage: true });
});

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("add gene", async ({ page }) => {
    await page.goto("/panels/1/gene/add");
    await expect(page).toHaveScreenshot("add-gene.png", { fullPage: true });
  });
});

test.describe(() => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test("add panel", async ({ page }) => {
    await page.goto("/panels/create/");
    await expect(page).toHaveScreenshot("add-panel.png", { fullPage: true });
  });
});

test("403 error", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2024-01-01T00:00:00"));

  await page.goto("/panels/create/");

  await expect(page).toHaveScreenshot("403.png", { fullPage: true });
});
