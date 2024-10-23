import { Browser, expect, Page } from "@playwright/test";
import {
  GeneReview,
  GeneReviewComment,
  NewGeneReview,
  NewGeneReviewComment,
  ReviewGeneForm,
} from "./gene-review";
import { NewPanel, NewPanelForm, Panel } from "./panel";
import { AddGeneForm, NewPanelGene, PanelGene } from "./panel-gene";

// Manage panels for use as fixtures in tests
export class Panels {
  readonly pages: Pages;
  panels: Map<string, Panel>;
  panelGenes: Map<string, PanelGene>;
  geneReviews: Map<string, GeneReview>;
  geneReviewComments: Map<string, GeneReviewComment>;

  constructor(pages: Pages) {
    this.pages = pages;
    this.panels = new Map();
    this.panelGenes = new Map();
    this.geneReviews = new Map();
    this.geneReviewComments = new Map();
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

    // The panel version cannot be set directly on creation
    // however we can verify that it matches the expected
    // initial state
    if (panel.version) {
      await expect
        .soft(
          page
            .getByRole("heading")
            .filter({ hasText: `(Version ${panel.version})` })
        )
        .toBeVisible();
    }

    const match = page.url().match(`https?:\/\/[^\/]+\/panels\/(\\d+)\/`);
    if (match === null) {
      throw Error(`URL is incorrect: ${page.url()}`);
    }
    const id = match[1];

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
    const href = await page
      .getByRole("link", { name: "Delete", exact: true })
      .getAttribute("href");

    if (!href) {
      throw new Error("href not found");
    }

    const match = href.match(
      `\/panels\/${panel.id}\/gene\/${panelGene.symbol}/delete_evaluation/(\\d+)\/`
    );
    if (match === null) {
      throw Error(`URL is incorrect: ${href}`);
    }
    const id = match[1];

    this.registerGeneReview({ ...review, id });

    return id;
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
