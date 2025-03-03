import { expect, Page } from "@playwright/test";
import { TestIdentifiable } from "./types";

export interface NewReleasePanel extends TestIdentifiable {
  testId: string;
  releaseTestId: string;
  panelTestId: string;
  promote: boolean;
}

export interface ReleasePanel extends NewReleasePanel {}

export const parseNewReleasePanel = (
  data: Record<string, string>
): NewReleasePanel => {
  return {
    testId: data["ID"],
    releaseTestId: data["Release ID"],
    panelTestId: data["Panel ID"],
    promote: data["Promote"] === "true" ? true : false,
  };
};

export class ImportReleasePanelsPage {
  readonly page: Page;
  readonly releaseId: string;

  constructor(page: Page, releaseId: string) {
    this.page = page;
    this.releaseId = releaseId;
  }

  async goto() {
    await this.page.goto(`/releases/${this.releaseId}/panels/import/`);
  }

  async importFromCsv(content: string) {
    const fileChooserPromise = this.page.waitForEvent("filechooser");
    await this.page.getByLabel("File to import").click();
    const fileChooser = await fileChooserPromise;

    await fileChooser.setFiles({
      name: "panels.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(content),
    });

    await this.page.getByLabel("Format").selectOption("csv");

    await this.page.getByRole("button", { name: "Import" }).click();

    await expect(
      this.page
        .getByRole("heading", { name: "Release Panels", exact: true })
        .or(this.page.getByText("There are issues with the submission."))
    ).toBeVisible();
  }
}

export class ReleasePanelListPage {
  readonly page: Page;
  readonly releaseId: string;

  constructor(page: Page, releaseId: string) {
    this.page = page;
    this.releaseId = releaseId;
  }

  async goto() {
    await this.page.goto(`/releases/${this.releaseId}/panels/`);
  }

  async search(term: string) {
    await this.page.getByPlaceholder("Search").pressSequentially(term);
  }

  async find({
    search,
    statuses,
    types,
  }: {
    search?: string;
    statuses?: string[];
    types?: string[];
  }) {
    if (search) {
      await this.search(search);
    }

    if (statuses) {
      for (const status of statuses) {
        await this.page.getByLabel(status).check();
      }
    }

    if (types) {
      for (const type of types) {
        await this.page.getByLabel(type).check();
      }
    }
  }
}
