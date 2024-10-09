import { expect, type Locator, type Page } from "@playwright/test";
import { PanelPage } from "./panel";
import { PanelForm, PanelInfo } from "./panel-form";

export class CreatePanelPage {
  readonly page: Page;
  readonly panelForm: PanelForm;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.panelForm = new PanelForm(page);
    this.submitButton = page.getByRole("button", { name: "Submit" });
  }

  async goto() {
    await this.page.goto("/panels/create/");
  }

  async createPanel(info: PanelInfo): PanelPage {
    await this.panelForm.setLevel4(info.level4);
    await this.panelForm.setDescription(info.level4);
    for (let name of info.childPanels) {
      await this.panelForm.addChildPanel(name);
    }
    await this.panelForm.setStatus(info.status);
    await this.submitButton.click();
    let re = new RegExp(`https?:\/\/[^\/]+\/panels\/(\\d+)\/`);
    await this.page.waitForURL(re, {
      timeout: 3000,
    });
    let panelId = this.page.url().match(re)[1];
    return new PanelPage(this.page, panelId);
  }
}
