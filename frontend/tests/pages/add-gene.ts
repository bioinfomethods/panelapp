import { expect, type Locator, type Page } from "@playwright/test";

export class AddGenePage {
  readonly panelId: string;
  readonly page: Page;
  readonly geneSymbolComboBox: Locator;
  readonly sourceInput: Locator;
  readonly modeOfInheritanceSelect: Locator;
  readonly addGeneButton: Locator;

  constructor(page: Page, panelId: string) {
    this.panelId = panelId;
    this.page = page;
    this.geneSymbolComboBox = page
      .getByTestId("gene-symbol")
      .locator("xpath=following-sibling::span/span[1]/span");
    this.sourceInput = page
      .getByTestId("source")
      .locator("xpath=following-sibling::span/span[1]/span/ul/li");
    this.modeOfInheritanceSelect = page.getByLabel("Mode of inheritance:");
    this.addGeneButton = page.getByRole("button", { name: "Add gene" });
  }

  async goto() {
    await this.page.goto(`/panels/${this.panelId}/gene/add`);
  }

  async addGene(info: GeneInfo) {
    await this.geneSymbolComboBox.click();
    let symbolSearchBox = this.page.getByRole("searchbox").nth(3);
    await symbolSearchBox.waitFor({ state: "visible" });
    await symbolSearchBox.pressSequentially(info.symbol);
    await this.page.getByRole("option", { name: info.symbol }).click();

    await this.sourceInput.click();
    await this.sourceInput.pressSequentially(info.source);
    await this.page
      .getByRole("option", { name: info.source, exact: true })
      .click();

    await this.modeOfInheritanceSelect.selectOption(info.modeOfInheritance);

    await this.addGeneButton.click();
    await this.page.waitForURL(
      `**/panels/${this.panelId}/gene/${info.symbol}/`,
      { timeout: 3000 }
    );
  }
}

interface GeneInfo {
  symbol: string;
  source: string;
  modeOfInheritance: string;
}
