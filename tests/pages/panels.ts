import { expect, type Locator, type Page } from "@playwright/test";

export class PanelsPage {
  readonly page: Page;
  readonly filterInput: Locator;

  constructor(page: Page) {
    this.page = page;
    this.filterInput = page.getByPlaceholder("Filter panels");
  }

  async goto() {
    await this.page.goto("/panels/");
  }

  async findPanel(name: string): PanelInfo {
    await this.filterInput.pressSequentially(name);
    let link = await this.page.getByRole("link", { name });
    try {
      await link.waitFor({ state: "visible", timeout: 1000 });
    } catch (e) {
      await this.filterInput.clear();
      return null;
    }
    let href = await link.getAttribute("href");
    let id = href.split("/").at(-2);
    await this.filterInput.clear();
    return {
      id,
    };
  }

  async unlockPanel(id: string) {
    let unlockButton = this.page.getByTestId(`unlock-panel-${id}`);
    await unlockButton.click();
    await unlockButton.waitFor({ state: "hidden", timeout: 1500 });
  }

  async deletePanel(id: string) {
    let deleteButton = this.page.getByTestId(`delete-panel-${id}`);
    await deleteButton.click();
    await deleteButton.waitFor({ state: "hidden", timeout: 1500 });
  }
}

interface PanelInfo {
  id: string;
}
