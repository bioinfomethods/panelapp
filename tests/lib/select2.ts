import { Page } from "@playwright/test";

export class Select2Multiple {
  readonly page: Page;
  readonly label: string;

  constructor(page: Page, label: string) {
    this.page = page;
    this.label = label;
  }

  async select(name: string) {
    await this.page
      .locator("form div")
      .filter({ hasText: this.label })
      .getByRole("combobox")
      .click();
    await this.page
      .locator("form div")
      .filter({ hasText: this.label })
      .getByRole("list")
      .pressSequentially(name);
    await this.page.getByRole("option", { name }).click();
  }
}
