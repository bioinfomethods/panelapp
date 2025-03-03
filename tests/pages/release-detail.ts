import { Locator, type Page } from "@playwright/test";
import { ManageReleasePage } from "./release-manage";

export class ReleaseDetailPage {
  readonly page: Page;
  readonly releaseId: string;
  readonly manageButton: Locator;

  constructor(page: Page, releaseId: string) {
    this.page = page;
    this.releaseId = releaseId;
    this.manageButton = page.getByRole("link", { name: "Manage" });
  }

  async goto() {
    await this.page.goto(`/panels/releases/${this.releaseId}/`);
  }

  async manage(): Promise<ManageReleasePage> {
    await this.manageButton.click();
    let re = new RegExp(
      `https?:\/\/[^\/]+\/panels\/releases\/${this.releaseId}\/manage/`
    );
    await this.page.waitForURL(re, {
      timeout: 3000,
    });
    return new ManageReleasePage(this.page, this.releaseId);
  }
}
