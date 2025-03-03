import { Browser, expect, Page } from "@playwright/test";
import { stringify } from "csv/sync";
import { ReviewFeedback } from "../pages/review-feedback";
import { GeneFeedback } from "./gene-feedback";
import {
  GeneReview,
  GeneReviewComment,
  NewGeneReview,
  NewGeneReviewComment,
  ReviewGeneForm,
} from "./gene-review";
import { NewPanel, NewPanelForm, Panel } from "./panel";
import { AddGeneForm, NewPanelGene, PanelGene } from "./panel-gene";
import { AddRegionForm, NewPanelRegion, PanelRegion } from "./panel-region";
import { AddStrForm, NewPanelStr, PanelStr } from "./panel-str";
import {
  NewRegionReview,
  RegionReview,
  ReviewRegionForm,
} from "./region-review";
import { NewRelease, NewReleaseForm, Release } from "./release";
import { NewReleasePanel, ReleasePanel } from "./release-panel";
import {
  NewStrReview,
  ReviewStrForm,
  StrReview,
  StrReviewComment,
} from "./str-review";

// Manage panels for use as fixtures in tests
export class Panels {
  readonly pages: Pages;
  panels: Map<string, Panel>;
  panelGenes: Map<string, PanelGene>;
  geneReviews: Map<string, GeneReview>;
  geneReviewComments: Map<string, GeneReviewComment>;
  panelStrs: Map<string, PanelStr>;
  strReviews: Map<string, StrReview>;
  strReviewComments: Map<string, StrReviewComment>;
  panelRegions: Map<string, PanelRegion>;
  regionReviews: Map<string, RegionReview>;
  releases: Map<string, Release>;
  releasePanels: Map<string, ReleasePanel>;

  constructor(pages: Pages) {
    this.pages = pages;
    this.panels = new Map();
    this.panelGenes = new Map();
    this.geneReviews = new Map();
    this.geneReviewComments = new Map();
    this.panelStrs = new Map();
    this.strReviews = new Map();
    this.strReviewComments = new Map();
    this.panelRegions = new Map();
    this.regionReviews = new Map();
    this.releases = new Map();
    this.releasePanels = new Map();
  }

  registerPanel(panel: Panel) {
    this.panels.set(panel.testId, panel);
  }

  registerPanelGene(panelGene: PanelGene) {
    this.panelGenes.set(panelGene.testId, panelGene);
  }

  registerGeneReview(geneReview: GeneReview) {
    this.geneReviews.set(geneReview.testId, geneReview);
  }

  registerGeneReviewComment(comment: GeneReviewComment) {
    this.geneReviewComments.set(comment.testId, comment);
  }

  registerPanelStr(panelStr: PanelStr) {
    this.panelStrs.set(panelStr.testId, panelStr);
  }

  registerStrReview(strReview: StrReview) {
    this.strReviews.set(strReview.testId, strReview);
  }

  registerPanelRegion(panelRegion: PanelRegion) {
    this.panelRegions.set(panelRegion.testId, panelRegion);
  }

  registerRegionReview(regionReview: RegionReview) {
    this.regionReviews.set(regionReview.testId, regionReview);
  }

  registerRelease(release: Release) {
    this.releases.set(release.testId, release);
  }

  registerReleasePanel(releasePanel: ReleasePanel) {
    this.releasePanels.set(releasePanel.testId, releasePanel);
  }

  async delete(testId: string) {
    const panel = this.panels.get(testId);
    if (!panel) {
      throw Error("Panel not found");
    }
    const page = await this.pages.get_or_create("admin");

    const response = await page.request.get(`/panels/${panel.id}/delete`, {
      headers: { "x-requested-with": "XMLHttpRequest" },
    });
    expect(response.ok()).toBeTruthy();

    this.panels.delete(testId);
  }

  async create(panel: NewPanel): Promise<string> {
    const page = await this.pages.get_or_create(panel.createdBy);

    await page.goto("/panels/create/");

    let form = new NewPanelForm(page);
    await form.fill(panel);
    await form.submit();

    await expect
      .soft(page.getByText("Successfully added a new panel"))
      .toBeVisible();

    const match = page.url().match(`https?://[^/]+/panels/(\\d+)/`);
    if (match === null) {
      throw Error(`URL is incorrect: ${page.url()}`);
    }
    const id = match[1];

    if (panel.comment) {
      // Can only add a comment by promoting the panel
      await page
        .getByPlaceholder("Comment about this new version")
        .fill(panel.comment);
      await page.getByRole("button", { name: "Increase Version" }).click();
    }

    // The panel version cannot be set directly on creation
    // however we can verify that it matches the expected
    // initial state
    if (panel.version) {
      await expect
        .soft(
          page
            .getByRole("heading")
            .filter({ hasText: `(Version ${panel.version})` }),
        )
        .toBeVisible();
    }

    this.registerPanel({ ...panel, id });
    return id;
  }

  async addPanelGene(gene: NewPanelGene) {
    const panel = this.panels.get(gene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    const page = await this.pages.get_or_create("admin");

    await page.goto(`/panels/${panel.id}/gene/add`);

    let form = new AddGeneForm(page);

    await form.fill(gene);
    await form.submit();

    await expect(page.getByText("Successfully added a new gene")).toBeVisible();

    this.registerPanelGene(gene);
  }

  async addPanelStr(str: NewPanelStr) {
    const panel = this.panels.get(str.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    const page = await this.pages.get_or_create("admin");

    await page.goto(`/panels/${panel.id}/str/add`);

    let form = new AddStrForm(page);

    await form.fill(str);
    await form.submit();

    await expect(page.getByText("Successfully added a new str")).toBeVisible();

    this.registerPanelStr(str);
  }

  async addPanelRegion(region: NewPanelRegion) {
    const panel = this.panels.get(region.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    const page = await this.pages.get_or_create("admin");

    await page.goto(`/panels/${panel.id}/region/add`);

    let form = new AddRegionForm(page);

    await form.fill(region);
    await form.submit();

    await expect(
      page.getByText("Successfully added a new region"),
    ).toBeVisible();

    this.registerPanelRegion(region);
  }

  async reviewGene(review: NewGeneReview): Promise<string> {
    const panelGene = this.panelGenes.get(review.panelGeneTestId);
    if (!panelGene) {
      throw Error("Panel Gene not found");
    }

    const panel = this.panels.get(panelGene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    const page = await this.pages.get_or_create(review.createdBy);

    await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/`);

    let form = new ReviewGeneForm(page);

    await form.fill(review);
    await form.submit();

    await expect(page.getByText("Successfully reviewed gene")).toBeVisible();

    // This locator is unique as there can only be one review per user
    // and the Delete button is only displayed for the user who owns
    // the review.
    const url = await page
      .getByRole("link", { name: "Delete", exact: true })
      .getAttribute("hx-get");

    if (!url) {
      throw new Error("url not found");
    }

    const match = url.match(
      `\/panels\/${panel.id}\/gene\/${panelGene.symbol}/delete_evaluation/(\\d+)\/`,
    );
    if (match === null) {
      throw Error(`URL is incorrect: ${url}`);
    }
    const id = match[1];

    this.registerGeneReview({ ...review, id });

    return id;
  }

  async reviewStr(review: NewStrReview): Promise<string> {
    const panelStr = this.panelStrs.get(review.panelStrTestId);
    if (!panelStr) {
      throw Error("Panel Str not found");
    }

    const panel = this.panels.get(panelStr.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    const page = await this.pages.get_or_create(review.createdBy);

    await page.goto(`/panels/${panel.id}/str/${panelStr.name}/`);

    let form = new ReviewStrForm(page);

    await form.fill(review);
    await form.submit();

    await expect(page.getByText("Successfully reviewed str")).toBeVisible();

    // This locator is unique as there can only be one review per user
    // and the Delete button is only displayed for the user who owns
    // the review.
    const url = await page
      .getByRole("link", { name: "Delete", exact: true })
      .getAttribute("hx-get");

    if (!url) {
      throw new Error("url not found");
    }

    const match = url.match(
      `/panels/${panel.id}/str/${panelStr.name}/delete_evaluation/(\\d+)/`,
    );
    if (match === null) {
      throw Error(`URL is incorrect: ${url}`);
    }
    const id = match[1];

    this.registerStrReview({ ...review, id });

    return id;
  }

  async reviewRegion(review: NewRegionReview): Promise<string> {
    const panelRegion = this.panelRegions.get(review.panelRegionTestId);
    if (!panelRegion) {
      throw Error("Panel Region not found");
    }

    const panel = this.panels.get(panelRegion.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    const page = await this.pages.get_or_create(review.createdBy);

    await page.goto(`/panels/${panel.id}/region/${panelRegion.name}/`);

    let form = new ReviewRegionForm(page);

    await form.fill(review);
    await form.submit();

    await expect(page.getByText("Successfully reviewed region")).toBeVisible();

    // This locator is unique as there can only be one review per user
    // and the Delete button is only displayed for the user who owns
    // the review.
    const url = await page
      .getByRole("link", { name: "Delete", exact: true })
      .getAttribute("hx-get");

    if (!url) {
      throw new Error("url not found");
    }

    const match = url.match(
      `/panels/${panel.id}/region/${panelRegion.name}/delete_evaluation/(\\d+)/`,
    );
    if (match === null) {
      throw Error(`URL is incorrect: ${url}`);
    }
    const id = match[1];

    this.registerRegionReview({ ...review, id });

    return id;
  }

  async reviewGeneFeedback(feedback: GeneFeedback): Promise<void> {
    const panelGene = this.panelGenes.get(feedback.panelGeneTestId);
    if (!panelGene) {
      throw Error("Panel Gene not found");
    }
    const panel = this.panels.get(panelGene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    const page = await this.pages.get_or_create(feedback.by);

    await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/#!review`);

    const feedbackPage = new ReviewFeedback(page);

    if (feedback.deleteComments) {
      for (const deleteComment of feedback.deleteComments) {
        const deleteButton = page
          .locator("blockquote")
          .filter({
            hasText: new RegExp(`Comment on.+: ${deleteComment.comment}`),
          })
          .getByRole("button");

        await deleteButton.click();
        await expect(deleteButton).not.toBeVisible();
      }
    }

    if (feedback.tags) {
      await feedbackPage.setTags(feedback.tags);
      await expect(page.getByText(/Saved at \d\d:\d\d:\d\d/)).toBeVisible();
    }

    if (feedback.rating) {
      await feedbackPage.setRating(
        feedback.rating.rating,
        feedback.rating.comment,
      );
    }
  }

  async addGeneReviewComment(comment: NewGeneReviewComment): Promise<string> {
    const review = this.geneReviews.get(comment.reviewTestId);
    if (!review) {
      throw Error("Review not found");
    }
    const panelGene = this.panelGenes.get(review.panelGeneTestId);
    if (!panelGene) {
      throw Error("Panel Gene not found");
    }
    const panel = this.panels.get(panelGene.panelTestId);
    if (!panel) {
      throw Error("Panel not found");
    }

    const page = await this.pages.get_or_create(comment.createdBy);

    await page.goto(`/panels/${panel.id}/gene/${panelGene.symbol}/`);

    let form = new ReviewGeneForm(page);
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

    this.registerGeneReviewComment({ ...comment, id });

    return id;
  }

  async createRelease(release: NewRelease) {
    const page = await this.pages.get_or_create(release.createdBy);

    await page.goto("/releases/create/");

    let form = new NewReleaseForm(page);
    await form.fill(release);
    await form.submit();

    await expect(
      page.getByRole("heading", { name: release.name }),
    ).toBeVisible();

    const match = page.url().match(`https?://[^/]+/releases/(\\d+)/`);
    if (match === null) {
      throw Error(`URL is incorrect: ${page.url()}`);
    }
    const id = match[1];

    this.registerRelease({ ...release, id });
    return id;
  }

  async deployRelease(testId: string) {
    const release = this.releases.get(testId);
    if (!release) {
      throw new Error("Release not found");
    }

    const page = await this.pages.get_or_create("admin");

    await page.goto(`/releases/${release.id}/deployment/`);

    page.on("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Deploy" }).click();

    await expect(page.getByText("DONE")).toBeVisible({ timeout: 15000 });
  }

  async renameRelease(testId: string, name: string) {
    const release = this.releases.get(testId);
    if (!release) {
      throw Error("Release not found");
    }
    const page = await this.pages.get_or_create("admin");

    await page.goto(`/releases/${release.id}/edit/`);

    await page.getByPlaceholder("Name").fill(name);

    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.getByRole("heading", { name })).toBeVisible();

    release.name = name;
  }

  async setReleasePanels(releasePanels: NewReleasePanel[]) {
    const groupedByRelease = releasePanels.reduce((acc, x) => {
      acc[x.releaseTestId] = acc[x.releaseTestId] || [];
      acc[x.releaseTestId].push(x);
      return acc;
    }, {});

    const page = await this.pages.get_or_create("admin");

    for (const releaseTestId of Object.keys(groupedByRelease)) {
      const release = this.releases.get(releaseTestId);
      if (!release) {
        throw Error("Release not found");
      }
      const releasePanelsByRelease = groupedByRelease[releaseTestId];

      const fields = ["Panel ID", "Promote"];
      const records = releasePanelsByRelease.map((x) => {
        // Convert test panel id to actual panel id
        const panel = this.panels.get(x.panelTestId);
        if (!panel) {
          throw Error("Panel not found");
        }
        return { "Panel ID": panel.id, Promote: x.promote.toString() };
      });

      const rows = records.map((rec) => fields.map((field) => rec[field]));

      const encoded = stringify([fields].concat(rows));

      await page.goto(`/releases/${release.id}/panels/import/`);

      const fileChooserPromise = page.waitForEvent("filechooser");
      await page.getByLabel("File to import").click();
      const fileChooser = await fileChooserPromise;

      await fileChooser.setFiles({
        name: "panels.csv",
        mimeType: "text/csv",
        buffer: Buffer.from(encoded),
      });

      await page.getByLabel("Format").selectOption("csv");

      await page.getByRole("button", { name: "Import" }).click();

      await expect(
        page.getByRole("heading", { name: "Release Panels" }),
      ).toBeVisible();
    }
  }

  async dispose() {
    const panels = new Map(this.panels);
    for (const id of panels.keys()) {
      await this.delete(id);
    }
  }
}

export class Pages {
  readonly browser: Browser;
  pages: Map<string, Page>;

  constructor(browser: Browser) {
    this.browser = browser;
    this.pages = new Map();
  }

  async create(username: string): Promise<Page> {
    if (this.pages.has(username)) {
      throw new Error(`Page already exists: '${username}'`);
    }

    const page = await (
      await this.browser.newContext({
        storageState: `playwright/.auth/${username}.json`,
      })
    ).newPage();
    this.pages.set(username, page);
    return page;
  }

  get(name: string): Page | undefined {
    return this.pages.get(name);
  }

  async get_or_create(username: string): Promise<Page> {
    let page = this.get(username);
    if (page) {
      return page;
    }
    return await this.create(username);
  }

  async dispose() {
    for (const page of this.pages.values()) {
      await page.close();
    }
  }
}
