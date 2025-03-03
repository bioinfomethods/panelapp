import { type Locator, type Page } from "@playwright/test";
import { ReleaseDetailPage } from "./release-detail";

export interface ReleaseInfo {
  name: string;
}

export class CreateReleaseForm {
  readonly page: Page;
  readonly nameInput: Locator;
  readonly createButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.nameInput = page.getByPlaceholder("Name");
    this.createButton = page.getByRole("button", { name: "Create" });
  }

  async setName(value: string) {
    await this.nameInput.fill(value);
  }

  async submit() {
    await this.createButton.click();
  }
}

export class CreateReleasePage {
  readonly page: Page;
  readonly form: CreateReleaseForm;
  readonly createButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.form = new CreateReleaseForm(page);
    this.createButton = page.getByRole("button", { name: "Create" });
  }

  async goto() {
    await this.page.goto("/panels/releases/create/");
  }

  async create(info: ReleaseInfo): Promise<ReleaseDetailPage> {
    await this.form.setName(info.name);
    await this.form.submit();
    let re = new RegExp(`https?:\/\/[^\/]+\/panels\/releases\/(\\d+)\/`);
    await this.page.waitForURL(re, {
      timeout: 3000,
    });
    let releaseId = this.page.url().match(re)[1];
    return new ReleaseDetailPage(this.page, releaseId);
  }
}
