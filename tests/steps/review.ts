import { expect } from "@playwright/test";
import { DataTable } from "playwright-bdd";
import { Given, Then, When } from ".";
import {
  parseNewGeneReview,
  parseNewGeneReviewComment,
  ReviewGeneForm,
} from "../lib/gene-review";
import { parseNewRegionReview, ReviewRegionForm } from "../lib/region-review";
import { parseNewStrReview, ReviewStrForm } from "../lib/str-review";
import { ReviewFeedback } from "../pages/review-feedback";

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

  const url = await deleteButton.getAttribute("hx-get");
  if (!url) {
    throw Error("url is null");
  }

  const match = url.match(
    `\/panels\/${panel.id}\/gene\/${panelGene.symbol}/delete_evaluation/(\\d+)\/`
  );
  if (match === null) {
    throw Error(`URL is incorrect: ${url}`);
  }
  const id = match[1];

  panels.registerGeneReview({ ...review, id });
});

When("I review the str", async ({ panels, page }, data: DataTable) => {
  const panelStrTestId = data.hashes()[0]["Panel Str ID"];
  const panelStr = panels.panelStrs.get(panelStrTestId);
  if (!panelStr) {
    throw Error("Panel Str not found");
  }
  const panel = panels.panels.get(panelStr.panelTestId);
  if (!panel) {
    throw Error("Panel not found");
  }

  await page.goto(`/panels/${panel.id}/str/${panelStr.name}/`);

  let form = new ReviewStrForm(page);
  const review = parseNewStrReview(data.hashes()[0]);
  await form.fill(review);
  await form.submit();
  await expect(page.getByText("Successfully reviewed str")).toBeVisible();

  const deleteButton = page.getByRole("link", {
    name: "Delete",
    exact: true,
  });

  await expect(deleteButton).toBeVisible();

  const url = await deleteButton.getAttribute("hx-get");
  if (!url) {
    throw Error("url is null");
  }

  const match = url.match(
    `/panels/${panel.id}/str/${panelStr.name}/delete_evaluation/(\\d+)/`
  );
  if (match === null) {
    throw Error(`URL is incorrect: ${url}`);
  }
  const id = match[1];

  panels.registerStrReview({ ...review, id });
});

When("I review the region", async ({ panels, page }, data: DataTable) => {
  const panelRegionTestId = data.hashes()[0]["Panel Region ID"];
  const panelRegion = panels.panelRegions.get(panelRegionTestId);
  if (!panelRegion) {
    throw Error("Panel Region not found");
  }
  const panel = panels.panels.get(panelRegion.panelTestId);
  if (!panel) {
    throw Error("Panel not found");
  }

  await page.goto(`/panels/${panel.id}/region/${panelRegion.name}/`);

  let form = new ReviewRegionForm(page);
  const review = parseNewRegionReview(data.hashes()[0]);
  await form.fill(review);
  await form.submit();
  await expect(page.getByText("Successfully reviewed region")).toBeVisible();

  const deleteButton = page.getByRole("link", {
    name: "Delete",
    exact: true,
  });

  await expect(deleteButton).toBeVisible();

  const url = await deleteButton.getAttribute("hx-get");
  if (!url) {
    throw Error("url is null");
  }

  const match = url.match(
    `/panels/${panel.id}/region/${panelRegion.name}/delete_evaluation/(\\d+)/`
  );
  if (match === null) {
    throw Error(`URL is incorrect: ${url}`);
  }
  const id = match[1];

  panels.registerRegionReview({ ...review, id });
});

Then("I see my review", async ({ page }) => {
  await expect(page.getByText("Your review")).toBeVisible();
  await expect(page.getByText("You reviewed")).toBeVisible();
});

Given("there are gene reviews", async ({ panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    await panels.reviewGene(parseNewGeneReview(row));
  }
});

Given("there are str reviews", async ({ panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    await panels.reviewStr(parseNewStrReview(row));
  }
});

Given("there are region reviews", async ({ panels }, data: DataTable) => {
  for (const row of data.hashes()) {
    await panels.reviewRegion(parseNewRegionReview(row));
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
  await expect(page.getByText("You reviewed")).not.toBeVisible();
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

When(
  "I edit the gene review comment",
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
      .getByRole("link", { name: "Edit your comment" })
      .click();

    await page
      .locator(`#comment_${geneReviewComment.id}`)
      .getByLabel("Comment:")
      .fill(data.hashes()[0]["Content"]);

    await page
      .locator(`#comment_${geneReviewComment.id}`)
      .getByRole("button", { name: "Save Changes" })
      .click();

    geneReviewComment.content = data.hashes()[0]["Content"];
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
  "I cannot edit the gene review comment",
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
          .getByRole("link", { name: "Edit comment" })
      )
      .not.toBeVisible();

    // Bypass the interface and try to edit the comment directly
    const response = await page.request.get(
      `/panels/${panel.id}/gene/${panelGene.symbol}/edit_comment/${geneReviewComment.id}/`
    );

    expect(response.ok()).toBeFalsy();
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

When(
  "I review feedback for gene {string}",
  async ({ page, panels }, testId: string, data: DataTable) => {
    const panelGene = panels.panelGenes.get(testId);
    if (!panelGene) {
      throw Error("Panel Gene not found");
    }
    const panel = panels.panels.get(panelGene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/#!review`);

    await expect(
      page.getByRole("heading", { name: "Review feedback" })
    ).toBeVisible();

    const feedback = new ReviewFeedback(page);

    for (const row of data.hashes()) {
      if (row["Property"] === "Tags") {
        await feedback.setTags(row["Value"].split(",").filter((x) => x));
      } else if (row["Property"] === "Rating") {
        await feedback.setRating(row["Value"], row["Comment"]);
      } else if (row["Property"] === "Mode of inheritance") {
        await feedback.setModeOfInheritance(row["Value"], row["Comment"]);
      } else if (row["Property"] === "Mode of pathogenicity") {
        await feedback.setModeOfPathogenicity(row["Value"], row["Comment"]);
      } else if (row["Property"] === "Publications") {
        await feedback.setPublications(
          row["Value"].split(";").filter((x) => x),
          row["Comment"]
        );
      } else if (row["Property"] === "Phenotypes") {
        await feedback.setPhenotypes(
          row["Value"].split(";").filter((x) => x),
          row["Comment"]
        );
      } else if (row["Property"] === "Ready") {
        if (row["Value"] === "true") {
          await feedback.markReady(row["Comment"]);
        } else if (row["Value"] === "false") {
          await feedback.markNotReady();
        } else {
          throw Error(`Invalid feedback ready value: ${row["Value"]}`);
        }
      } else {
        throw Error(`Invalid feedback property: ${row["Property"]}`);
      }
    }
  }
);

When(
  "I review feedback for str {string}",
  async ({ page, panels }, testId: string, data: DataTable) => {
    const panelStr = panels.panelStrs.get(testId);
    if (!panelStr) {
      throw Error("Panel Str not found");
    }
    const panel = panels.panels.get(panelStr.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/${panel.id}/str/${panelStr.name}/#!review`);

    await expect(
      page.getByRole("heading", { name: "Review feedback" })
    ).toBeVisible();

    const feedback = new ReviewFeedback(page);

    for (const row of data.hashes()) {
      if (row["Property"] === "Tags") {
        await feedback.setTags(row["Value"].split(",").filter((x) => x));
      } else if (row["Property"] === "Rating") {
        await feedback.setRating(row["Value"], row["Comment"]);
      } else if (row["Property"] === "Mode of inheritance") {
        await feedback.setModeOfInheritance(row["Value"], row["Comment"]);
      } else if (row["Property"] === "Publications") {
        await feedback.setPublications(
          row["Value"].split(";").filter((x) => x),
          row["Comment"]
        );
      } else if (row["Property"] === "Phenotypes") {
        await feedback.setPhenotypes(
          row["Value"].split(";").filter((x) => x),
          row["Comment"]
        );
      } else if (row["Property"] === "Ready") {
        if (row["Value"] === "true") {
          await feedback.markReady(row["Comment"]);
        } else if (row["Value"] === "false") {
          await feedback.markNotReady();
        } else {
          throw Error(`Invalid feedback ready value: ${row["Value"]}`);
        }
      } else {
        throw Error(`Invalid feedback property: ${row["Property"]}`);
      }
    }
  }
);

When(
  "I review feedback for region {string}",
  async ({ page, panels }, testId: string, data: DataTable) => {
    const panelRegion = panels.panelRegions.get(testId);
    if (!panelRegion) {
      throw Error("Panel Gene not found");
    }
    const panel = panels.panels.get(panelRegion.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    await page.goto(`/panels/${panel.id}/region/${panelRegion.name}/#!review`);

    await expect(
      page.getByRole("heading", { name: "Review feedback" })
    ).toBeVisible();

    const feedback = new ReviewFeedback(page);

    for (const row of data.hashes()) {
      if (row["Property"] === "Tags") {
        await feedback.setTags(row["Value"].split(",").filter((x) => x));
      } else if (row["Property"] === "Rating") {
        await feedback.setRating(row["Value"], row["Comment"]);
      } else if (row["Property"] === "Mode of inheritance") {
        await feedback.setModeOfInheritance(row["Value"], row["Comment"]);
      } else if (row["Property"] === "Publications") {
        await feedback.setPublications(
          row["Value"].split(";").filter((x) => x),
          row["Comment"]
        );
      } else if (row["Property"] === "Phenotypes") {
        await feedback.setPhenotypes(
          row["Value"].split(";").filter((x) => x),
          row["Comment"]
        );
      } else if (row["Property"] === "Ready") {
        if (row["Value"] === "true") {
          await feedback.markReady(row["Comment"]);
        } else if (row["Value"] === "false") {
          await feedback.markNotReady();
        } else {
          throw Error(`Invalid feedback ready value: ${row["Value"]}`);
        }
      } else {
        throw Error(`Invalid feedback property: ${row["Property"]}`);
      }
    }
  }
);
