import { expect, type Locator, type Page } from "@playwright/test";
import { AddGenePage } from "./add-gene";
import { PanelForm, PanelInfo } from "./panel-form";

export class PanelPage {
  readonly page: Page;
  readonly editPanelButton: Locator;
  readonly addGeneButton: Locator;
  readonly panelForm: PanelForm;
  readonly saveButton: Locator;

  constructor(page: Page, panelId: string) {
    this.panelId = panelId;
    this.page = page;
    this.editPanelButton = page
      .getByRole("link")
      .filter({ hasText: "Edit panel" });
    this.addGeneButton = page.getByRole("link", {
      name: "+ Add a Gene to this panel",
    });
    this.panelForm = new PanelForm(page);
    this.saveButton = page.getByRole("button", { name: "Save" });
  }

  async goto() {
    await this.page.goto(`/panels/${this.panelId}/`);
  }

  async editPanel(): PanelForm {
    await this.editPanelButton.click();
    return this.panelForm;
  }

  async savePanel() {
    await this.saveButton.click();
  }

  async addGene(): AddGenePage {
    await this.addGeneButton.click();
    await this.page.waitForURL(`**/gene/add`, { timeout: 3000 });
    return new AddGenePage(this.page, this.panelId);
  }
}
