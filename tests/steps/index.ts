import { expect } from "@playwright/test";
import { createBdd, DataTable } from "playwright-bdd";
import {
  parseNewGeneReview,
  parseNewGeneReviewComment,
  ReviewGeneForm,
} from "../lib/gene-review";
import { LoginPage } from "../lib/login";
import {
  EditPanelForm,
  NewPanelForm,
  parseEditPanel,
  parseNewPanel,
} from "../lib/panel";
import { AddGeneForm, parseNewPanelGene } from "../lib/panel-gene";
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

When("I review the gene", async ({ panels, page }, data: DataTable) => {
  const panelGeneTestId = data.hashes()[0]["Panel Gene ID"];
  const panelGene = panels.panelGenes.get(panelGeneTestId);
  if (!panelGene) {
    throw Error("Panel Gene not found");
  }
  const panel = panels.panels.get(panelGene.panelTestId);
  if (!panel) {
    throw Error("Panel not found");
  }

  await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/`);

  let form = new ReviewGeneForm(page);
  const review = parseNewGeneReview(data.hashes()[0]);
  await form.fill(review);
  await form.submit();
  await expect(page.getByText("Successfully reviewed gene")).toBeVisible();

  const deleteButton = page.getByRole("link", {
    name: "Delete",
    exact: true,
  });

  await expect(deleteButton).toBeVisible();

  const href = await deleteButton.getAttribute("href");
  if (!href) {
    throw Error("href is null");
  }

  const match = href.match(
    `\/panels\/${panel.id}\/gene\/${panelGene.symbol}/delete_evaluation/(\\d+)\/`
  );
  if (match === null) {
    throw Error(`URL is incorrect: ${href}`);
  }
  const id = match[1];

  panels.registerGeneReview({ ...review, id });
});

Then("I see my review", async ({ page }) => {
  await expect(page.getByText("Your review")).toBeVisible();
});

Given("there are gene reviews", async ({ panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    await panels.reviewGene(parseNewGeneReview(row));
  }
});

When("I delete the gene review", async ({ panels, page }, data: DataTable) => {
  const geneReview = panels.geneReviews.get(data.hashes()[0]["Gene Review ID"]);
  if (!geneReview) {
    throw Error("Gene Review not found");
  }
  const panelGene = panels.panelGenes.get(geneReview.panelGeneTestId);
  if (!panelGene) {
    throw Error("Panel Gene not found");
  }
  const panel = panels.panels.get(panelGene.panelTestId);
  if (!panel) {
    throw Error("Panel not found");
  }

  await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/`);

  await page.getByRole("link", { name: "Delete", exact: true }).click();
});

Then("I do not see my review", async ({ page }) => {
  await expect(page.getByText("Your review")).not.toBeVisible();
});

When(
  "I create a gene review comment",
  async ({ panels, page }, data: DataTable) => {
    const geneReview = panels.geneReviews.get(
      data.hashes()[0]["Gene Review ID"]
    );
    if (!geneReview) {
      throw Error("Gene Review not found");
    }
    const panelGene = panels.panelGenes.get(geneReview.panelGeneTestId);
    if (!panelGene) {
      throw Error("Panel Gene not found");
    }
    const panel = panels.panels.get(panelGene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/`);

    let form = new ReviewGeneForm(page);
    const comment = parseNewGeneReviewComment(data.hashes()[0]);
    await form.fill({
      comments: comment.content,
    });
    await form.submit();

    await expect(page.getByText("Successfully reviewed gene")).toBeVisible();

    const element = page.getByText(`${comment.content} Created:`);

    await expect(element).toBeVisible();

    const match = (await element.getAttribute("id"))?.match("comment_(\\d+)");
    if (!match) {
      throw Error("Unrecognised comment id");
    }

    const id = match[1];

    panels.registerGeneReviewComment({ ...comment, id });
  }
);

Then(
  "I see the gene review comment",
  async ({ panels, page }, data: DataTable) => {
    const geneReviewComment = panels.geneReviewComments.get(
      data.hashes()[0]["Gene Review Comment ID"]
    );
    if (!geneReviewComment) {
      throw Error("Gene Review Comment not found");
    }

    await expect(
      page.getByText(`${geneReviewComment.content} Created:`)
    ).toBeVisible();
  }
);

Given("there are gene review comments", async ({ panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    await panels.addGeneReviewComment(parseNewGeneReviewComment(row));
  }
});

When(
  "I delete the gene review comment",
  async ({ panels, page }, data: DataTable) => {
    const geneReviewComment = panels.geneReviewComments.get(
      data.hashes()[0]["Gene Review Comment ID"]
    );
    if (!geneReviewComment) {
      throw Error("Gene Review Comment not found");
    }
    const geneReview = panels.geneReviews.get(geneReviewComment.reviewTestId);
    if (!geneReview) {
      throw Error("Gene Review not found");
    }
    const panelGene = panels.panelGenes.get(geneReview.panelGeneTestId);
    if (!panelGene) {
      throw Error("Panel Gene not found");
    }
    const panel = panels.panels.get(panelGene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/`);

    await page
      .locator(`#comment_${geneReviewComment.id}`)
      .getByRole("link", { name: "Delete comment" })
      .click();
  }
);

Then(
  "I do not see the gene review comment",
  async ({ panels, page }, data: DataTable) => {
    const geneReviewComment = panels.geneReviewComments.get(
      data.hashes()[0]["Gene Review Comment ID"]
    );
    if (!geneReviewComment) {
      throw Error("Gene Review not found");
    }

    await expect(
      page.getByText(`${geneReviewComment.content} Created:`)
    ).not.toBeVisible();
  }
);

Then(
  "I cannot delete the gene review",
  async ({ panels, page, accounts }, data: DataTable) => {
    const geneReview = panels.geneReviews.get(
      data.hashes()[0]["Gene Review ID"]
    );
    if (!geneReview) {
      throw Error("Gene Review not found");
    }
    const panelGene = panels.panelGenes.get(geneReview.panelGeneTestId);
    if (!panelGene) {
      throw Error("Panel Gene not found");
    }
    const panel = panels.panels.get(panelGene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/`);

    await expect
      .soft(page.getByRole("link", { name: "Delete", exact: true }))
      .not.toBeVisible();

    // Bypass the interface and try to delete the review directly
    await page.request.get(
      `/panels/${panel.id}/gene/${panelGene.symbol}/delete_evaluation/${geneReview.id}/`,
      {
        headers: { "x-requested-with": "XMLHttpRequest" },
      }
    );

    await page.reload();

    const account = accounts.get(geneReview.createdBy);
    if (!account) {
      throw Error("Account not found");
    }

    await expect
      .soft(
        page
          .locator("#evaluations div")
          .filter({ hasText: `${account.firstName} ${account.lastName}` })
          .first()
      )
      .toBeVisible();
  }
);

Then(
  "I cannot delete the gene review comment",
  async ({ panels, page }, data: DataTable) => {
    const geneReviewComment = panels.geneReviewComments.get(
      data.hashes()[0]["Gene Review Comment ID"]
    );
    if (!geneReviewComment) {
      throw Error("Gene Review Comment not found");
    }
    const geneReview = panels.geneReviews.get(geneReviewComment.reviewTestId);
    if (!geneReview) {
      throw Error("Gene Review not found");
    }
    const panelGene = panels.panelGenes.get(geneReview.panelGeneTestId);
    if (!panelGene) {
      throw Error("Panel Gene not found");
    }
    const panel = panels.panels.get(panelGene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/`);

    await expect
      .soft(
        page
          .locator(`#comment_${geneReviewComment.id}`)
          .getByRole("link", { name: "Delete comment" })
      )
      .not.toBeVisible();

    // Bypass the interface and try to delete the comment directly
    await page.request.get(
      `/panels/${panel.id}/gene/${panelGene.symbol}/delete_comment/${geneReviewComment.id}/`,
      {
        headers: { "x-requested-with": "XMLHttpRequest" },
      }
    );

    await page.reload();

    await expect
      .soft(page.getByText(`${geneReviewComment.content} Created:`))
      .toBeVisible();
  }
);

When("I am on the home page", async ({ page }) => {
  await page.goto("/");
});

When("I am on the panels page", async ({ page }) => {
  await page.goto("/panels/");
});
