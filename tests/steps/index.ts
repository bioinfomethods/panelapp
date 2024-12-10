import { expect } from "@playwright/test";
import { createBdd, DataTable } from "playwright-bdd";
import { LoginPage } from "../lib/login";
import {
  EditPanelForm,
  NewPanelForm,
  parseEditPanel,
  parseNewPanel,
} from "../lib/panel";
import { AddGeneForm, parseNewPanelGene } from "../lib/panel-gene";
import { parseNewPanelRegion } from "../lib/panel-region";
import { parseNewPanelStr } from "../lib/panel-str";
import { test } from "../lib/test";

export { test };

export const { Given, When, Then, Step } = createBdd(test);

Step("I log in as {string}", async ({ page, accounts }, username: string) => {
  const account = accounts.get(username);
  if (!account) {
    throw new Error(`Unrecognised username: ${username}`);
  }

  const login = new LoginPage(page);
  await login.goto();
  await login.login(username, account.password);
});

Step("I create a panel", async ({ page, panels }, data: DataTable) => {
  await page.goto("/panels/create/");

  let form = new NewPanelForm(page);
  const panel = parseNewPanel(data.hashes()[0]);
  await form.fill(panel);
  await form.submit();
  await expect(page.getByText("Successfully added a new panel")).toBeVisible();

  const match = page.url().match(`https?:\/\/[^\/]+\/panels\/(\\d+)\/`);
  if (match === null) {
    throw Error(`URL is incorrect: ${page.url()}`);
  }
  const id = match[1];

  panels.registerPanel({ ...panel, id });
});

Step("I edit the panel", async ({ page, panels }, data: DataTable) => {
  const panel = panels.panels.get(data.hashes()[0]["Panel ID"]);
  if (!panel) {
    throw Error("Panel not found");
  }

  const editPanel = parseEditPanel(data.hashes()[0]);

  await page.goto(`/panels/${panel.id}/`);

  await page.getByText("Edit panel").click();
  await expect(page.getByText("Update Information")).toBeVisible();

  const form = new EditPanelForm(page);
  await form.fill(editPanel);
  await form.submit();
  await expect(page.getByText("Successfully updated the panel")).toBeVisible();
});

Then("I see panels", async ({ page }, data: DataTable) => {
  await page.goto("/panels/");

  for (const row of data.hashes()) {
    await expect
      .soft(page.getByRole("link", { name: row["Level4"], exact: true }))
      .toBeVisible();

    if (row["Version"]) {
      await expect
        .soft(
          page.getByRole("cell", {
            name: row["Level4"],
          })
        )
        .toContainText(`Version ${row["Version"]}`);
    }
  }
});

Given(
  "I add a gene to the panel",
  async ({ page, panels }, data: DataTable) => {
    const panelGene = parseNewPanelGene(data.hashes()[0]);

    const panel = panels.panels.get(panelGene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/${panel.id}/gene/add`);

    let form = new AddGeneForm(page);

    await form.fill(panelGene);
    await form.submit();

    await expect(page.getByText("Successfully added a new gene")).toBeVisible();

    panels.registerPanelGene(panelGene);
  }
);

Then("I see panel genes", async ({ page, panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    const panel = panels.panels.get(row["Panel ID"]);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/entities/${row["Gene symbol"]}`);

    await expect
      .soft(
        page.getByRole("row", {
          name: `${row["Gene symbol"]} in ${panel.level4}`,
        })
      )
      .toBeVisible();

    if (row["Mode of inheritance"]) {
      await expect
        .soft(
          page
            .getByRole("row", {
              name: `${row["Gene symbol"]} in ${panel.level4}`,
            })
            .getByRole("cell")
            .nth(2)
        )
        .toContainText(row["Mode of inheritance"]);
    }

    if (row["Tags"]) {
      const tags = row["Tags"].split(",").filter((x) => x);
      for (const tag of tags) {
        await expect
          .soft(
            page
              .getByRole("row", {
                name: `${row["Gene symbol"]} in ${panel.level4}`,
              })
              .getByRole("cell")
              .nth(3)
              .getByText(tag)
          )
          .toBeVisible();
      }
    }

    await page.goto(`/panels/${panel.id}/gene/${row["Gene symbol"]}/#!details`);

    if (row["Tags"]) {
      for (const tag of row["Tags"].split(",").filter((x) => x)) {
        await expect(page.locator("dl").getByText(tag)).toBeVisible();
      }
    }

    if (row["Rating"]) {
      await expect(
        page.locator("#gene-banner-heading").getByText(row["Rating"])
      ).toBeVisible();
    }

    if (row["Mode of inheritance"]) {
      await expect(
        page.locator("dd").filter({ hasText: row["Mode of inheritance"] })
      ).toBeVisible();
    }

    if (row["Mode of pathogenicity"]) {
      await expect(
        page.locator("dd").filter({ hasText: row["Mode of pathogenicity"] })
      ).toBeVisible();
    }

    if (row["Publications"]) {
      for (const publication of row["Publications"]
        .split(";")
        .filter((x) => x)) {
        await expect(
          page
            .locator("#details-content")
            .getByText(publication, { exact: true })
        ).toBeVisible();
      }
    }

    if (row["Phenotypes"]) {
      for (const phenotype of row["Phenotypes"].split(";").filter((x) => x)) {
        await expect(
          page.locator("#details-content").getByText(phenotype, { exact: true })
        ).toBeVisible();
      }
    }

    if (row["Ready"]) {
      if (row["Ready"] === "true") {
        await expect(page.getByText("Ready for major version")).toBeVisible();
      } else if (row["Ready"] === "false") {
        await expect(
          page.getByText("Ready for major version")
        ).not.toBeVisible();
      } else {
        throw Error(`Invalid ready value: ${row["Ready"]}`);
      }
    }
  }
});

Then("I do not see panel genes", async ({ page, panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    const panel = panels.panels.get(row["Panel ID"]);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/entities/${row["Gene symbol"]}`);

    if (row["Mode of inheritance"]) {
      await expect
        .soft(
          page
            .getByRole("row", {
              name: `${row["Gene symbol"]} in ${panel.level4}`,
            })
            .getByRole("cell")
            .nth(2)
            .filter({ hasText: row["Mode of inheritance"] })
        )
        .not.toBeVisible();
    }
  }
});

Then("I see panel strs", async ({ page, panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    const panel = panels.panels.get(row["Panel ID"]);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/entities/${row["Name"]}`);

    await expect
      .soft(
        page.getByRole("row", {
          name: `${row["Name"]} STR in ${panel.level4}`,
        })
      )
      .toBeVisible();

    if (row["Mode of inheritance"]) {
      await expect
        .soft(
          page
            .getByRole("row", {
              name: `${row["Name"]} STR in ${panel.level4}`,
            })
            .getByRole("cell")
            .nth(2)
        )
        .toContainText(row["Mode of inheritance"]);
    }

    if (row["Tags"]) {
      const tags = row["Tags"].split(",").filter((x) => x);
      for (const tag of tags) {
        await expect
          .soft(
            page
              .getByRole("row", {
                name: `${row["Name"]} STR in ${panel.level4}`,
              })
              .getByRole("cell")
              .nth(3)
              .getByText(tag)
          )
          .toBeVisible();
      }
    }

    await page.goto(`/panels/${panel.id}/str/${row["Name"]}/#!details`);

    if (row["Tags"]) {
      for (const tag of row["Tags"].split(",").filter((x) => x)) {
        await expect(page.locator("dl").getByText(tag)).toBeVisible();
      }
    }

    if (row["Rating"]) {
      await expect(
        page.locator("#gene-banner-heading").getByText(row["Rating"])
      ).toBeVisible();
    }

    if (row["Mode of inheritance"]) {
      await expect(
        page.locator("dd").filter({ hasText: row["Mode of inheritance"] })
      ).toBeVisible();
    }

    if (row["Mode of pathogenicity"]) {
      await expect(
        page.locator("dd").filter({ hasText: row["Mode of pathogenicity"] })
      ).toBeVisible();
    }

    if (row["Publications"]) {
      for (const publication of row["Publications"]
        .split(";")
        .filter((x) => x)) {
        await expect(
          page
            .locator("#details-content")
            .getByText(publication, { exact: true })
        ).toBeVisible();
      }
    }

    if (row["Phenotypes"]) {
      for (const phenotype of row["Phenotypes"].split(";").filter((x) => x)) {
        await expect(
          page.locator("#details-content").getByText(phenotype, { exact: true })
        ).toBeVisible();
      }
    }

    if (row["Ready"]) {
      if (row["Ready"] === "true") {
        await expect(page.getByText("Ready for major version")).toBeVisible();
      } else if (row["Ready"] === "false") {
        await expect(
          page.getByText("Ready for major version")
        ).not.toBeVisible();
      } else {
        throw Error(`Invalid ready value: ${row["Ready"]}`);
      }
    }
  }
});

Then("I see panel regions", async ({ page, panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    const panel = panels.panels.get(row["Panel ID"]);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/entities/${row["Name"]}`);

    await expect
      .soft(
        page.getByRole("row", {
          name: `${row["Name"]} Region in ${panel.level4}`,
        })
      )
      .toBeVisible();

    if (row["Mode of inheritance"]) {
      await expect
        .soft(
          page
            .getByRole("row", {
              name: `${row["Name"]} Region in ${panel.level4}`,
            })
            .getByRole("cell")
            .nth(2)
        )
        .toContainText(row["Mode of inheritance"]);
    }

    if (row["Tags"]) {
      const tags = row["Tags"].split(",").filter((x) => x);
      for (const tag of tags) {
        await expect
          .soft(
            page
              .getByRole("row", {
                name: `${row["Name"]} Region in ${panel.level4}`,
              })
              .getByRole("cell")
              .nth(3)
              .getByText(tag)
          )
          .toBeVisible();
      }
    }

    await page.goto(`/panels/${panel.id}/region/${row["Name"]}/#!details`);

    if (row["Tags"]) {
      for (const tag of row["Tags"].split(",").filter((x) => x)) {
        await expect(page.locator("dl").getByText(tag)).toBeVisible();
      }
    }

    if (row["Rating"]) {
      await expect(
        page.locator("#gene-banner-heading").getByText(row["Rating"])
      ).toBeVisible();
    }

    if (row["Mode of inheritance"]) {
      await expect(
        page.locator("dd").filter({ hasText: row["Mode of inheritance"] })
      ).toBeVisible();
    }

    if (row["Mode of pathogenicity"]) {
      await expect(
        page.locator("dd").filter({ hasText: row["Mode of pathogenicity"] })
      ).toBeVisible();
    }

    if (row["Publications"]) {
      for (const publication of row["Publications"]
        .split(";")
        .filter((x) => x)) {
        await expect(
          page
            .locator("#details-content")
            .getByText(publication, { exact: true })
        ).toBeVisible();
      }
    }

    if (row["Phenotypes"]) {
      for (const phenotype of row["Phenotypes"].split(";").filter((x) => x)) {
        await expect(
          page.locator("#details-content").getByText(phenotype, { exact: true })
        ).toBeVisible();
      }
    }

    if (row["Ready"]) {
      if (row["Ready"] === "true") {
        await expect(page.getByText("Ready for major version")).toBeVisible();
      } else if (row["Ready"] === "false") {
        await expect(
          page.getByText("Ready for major version")
        ).not.toBeVisible();
      } else {
        throw Error(`Invalid ready value: ${row["Ready"]}`);
      }
    }
  }
});

Given("there are panels", async ({ panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    await panels.create(parseNewPanel(row));
  }
});

Given("there are panel genes", async ({ panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    await panels.addPanelGene(parseNewPanelGene(row));
  }
});

Given("there are panel strs", async ({ panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    await panels.addPanelStr(parseNewPanelStr(row));
  }
});

Given("there are panel regions", async ({ panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    await panels.addPanelRegion(parseNewPanelRegion(row));
  }
});
