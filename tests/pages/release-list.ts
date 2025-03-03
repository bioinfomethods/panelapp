import { type Locator, type Page } from "@playwright/test";
import { ReleaseCreatePage } from "./release-create";

export class ReleaseListPage {
  readonly page: Page;
  readonly createButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.createButton = page.getByRole("link", { name: "Create" });
  }

  async goto() {
    await this.page.goto("/panels/releases/");
  }

  async create(): Promise<ReleaseCreatePage> {
    await this.createButton.click();
    await this.page.waitForURL("/panels/releases/create/", { timeout: 3000 });
    return new ReleaseCreatePage(this.page);
  }
}
