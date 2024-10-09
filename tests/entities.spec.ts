import { test, expect } from "@playwright/test";

test("filter by entity name", async ({ page }) => {
  await page.goto("/panels/entities/");
  await page.getByPlaceholder("Filter genes and genomic entities").click();
  // Use "pressSequentially" instead of "fill" because PanelApp listens for keyup events
  await page
    .getByPlaceholder("Filter genes and genomic entities")
    .pressSequentially("aaas");
  let entitiesList = page.locator("//ul[@id='entities-list']/li");
  let entities = [];
  for (let item of await entitiesList.all()) {
    let text = await item.textContent();
    let visible = await item.isVisible();
    entities.push({ text: text.trim(), visible: visible });
  }
  expect(entities).toEqual([
    { text: "AAAS", visible: true },
    { text: "BRCA1", visible: false },
    { text: "CCDC154", visible: false },
    { text: "DEFB115", visible: false },
    { text: "EIF3C", visible: false },
  ]);
});
