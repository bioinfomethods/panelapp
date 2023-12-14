import { expect, type Locator, type Page } from "@playwright/test";

export class PanelForm {
  readonly page: Page;
  readonly level4Input: Locator;
  readonly descriptionInput: Locator;
  readonly childPanelsInput: Locator;
  readonly statusSelect: Locator;

  constructor(page: Page) {
    this.page = page;
    this.level4Input = page.getByPlaceholder("Level4");
    this.descriptionInput = page.getByPlaceholder("Description");
    this.childPanelsInput = page
      .locator("form div")
      .filter({ hasText: "Child Panels" })
      .getByRole("combobox");
    this.statusSelect = page.getByLabel("Status");
    this.submitButton = page.getByRole("button", { name: "Submit" });
  }

  async setLevel4(value: string) {
    await this.level4Input.clear();
    await this.level4Input.pressSequentially(value);
  }

  async setDescription(value: string) {
    await this.descriptionInput.clear();
    await this.descriptionInput.pressSequentially(value);
  }

  async addChildPanel(name: string) {
    await this.childPanelsInput.pressSequentially(name);
    await this.page.getByRole("option").filter({ hasText: name }).click();
  }

  async setStatus(value: string) {
    await this.statusSelect.selectOption(value);
  }
}

interface PanelInfo {
  level4: string;
  description: string;
  childPanels: string[];
  status: string;
}
