import { Page } from "@playwright/test";
import { TestIdentifiable } from "./types";

export interface NewPanelGene extends TestIdentifiable {
  panelTestId: string;
  symbol: string;
  sources: string[];
  modeOfInheritance: string;
  modeOfPathogenicity?: string;
  penetrance?: string;
  publications?: string;
  phenotypes?: string;
  tags?: string[];
  transcripts?: string;
  additionalPanels?: string[];
  rating?: string;
  currentDiagnostic?: boolean;
  comments?: string;
}

export interface PanelGene extends NewPanelGene {}

export const parseNewPanelGene = (
  data: Record<string, string>
): NewPanelGene => {
  return {
    testId: data["ID"],
    panelTestId: data["Panel ID"],
    symbol: data["Gene symbol"],
    sources: data["Sources"].split(",").filter((x) => x),
    modeOfPathogenicity: data["Mode of pathogenicity"],
    modeOfInheritance: data["Mode of inheritance"],
    penetrance: data["Penetrance"],
    publications: data["Publications"],
    phenotypes: data["Phenotypes"],
    tags: data["Tags"]?.split(",").filter((x) => x),
    rating: data["Rating"],
    currentDiagnostic:
      data["Current diagnostic"] !== undefined
        ? data["Current diagnostic"].toLowerCase() === "yes"
        : undefined,
    comments: data["Comments"],
    additionalPanels: data["Additional panels"]?.split(",").filter((x) => x),
  };
};

export class AddGeneForm {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  get geneSymbolInput() {
    return this.page.getByLabel("", { exact: true });
  }

  get sourceInput() {
    return this.page
      .getByRole("group")
      .locator("div")
      .filter({ hasText: "Source: Source" })
      .getByRole("combobox");
  }

  get modeOfPathogenicityInput() {
    return this.page.getByLabel("Mode of pathogenicity:");
  }

  get modeOfInheritanceInput() {
    return this.page.getByLabel("Mode of inheritance:");
  }

  get penetranceInput() {
    return this.page.getByLabel("Penetrance:");
  }

  get publicationsInput() {
    return this.page.getByPlaceholder("Publications (PMID: 1234;4321)");
  }

  get phenotypesInput() {
    return this.page.getByPlaceholder("Phenotypes (separate using a");
  }

  get transcriptsInput() {
    return this.page.getByPlaceholder("Transcripts (separate using a");
  }

  get ratingInput() {
    return this.page.getByLabel("Rating");
  }

  get tagsInput() {
    return this.page
      .getByRole("group")
      .locator("div")
      .filter({ hasText: "Tags: Tags" })
      .getByRole("combobox");
  }

  get additionalPanelsInput() {
    return this.page
      .getByRole("group")
      .locator("div")
      .filter({ hasText: "Additional panels: Additional" })
      .getByRole("combobox");
  }

  get currentDiagnosticInput() {
    return this.page.getByLabel("Current diagnostic:");
  }

  get commentsInput() {
    return this.page.getByPlaceholder("Comments");
  }

  get submitButton() {
    return this.page.getByRole("button", { name: "Add gene" });
  }

  async setGeneSymbol(name: string) {
    await this.geneSymbolInput.click();
    await this.page.getByRole("searchbox").nth(3).pressSequentially(name);
    await this.page.getByRole("option", { name }).click();
  }

  async addSource(name: string) {
    await this.sourceInput.click();
    await this.sourceInput.pressSequentially(name);
    await this.page.getByRole("option", { name }).click();
  }

  async setModeOfPathogenicity(value: string) {
    await this.modeOfPathogenicityInput.selectOption(value);
  }

  async setModeOfInheritance(value: string) {
    await this.modeOfInheritanceInput.selectOption(value);
  }

  async setPenetrance(value: string) {
    await this.penetranceInput.selectOption(value);
  }

  async setPublications(value: string) {
    await this.publicationsInput.clear();
    await this.publicationsInput.pressSequentially(value);
  }

  async setPhenotypes(value: string) {
    await this.phenotypesInput.clear();
    await this.phenotypesInput.pressSequentially(value);
  }

  async addTag(name: string) {
    await this.tagsInput.click();
    await this.tagsInput.pressSequentially(name);
    await this.page.getByRole("option", { name }).click();
  }

  async setTranscripts(value: string) {
    await this.transcriptsInput.clear();
    await this.transcriptsInput.pressSequentially(value);
  }

  async addAdditionalPanel(name: string) {
    await this.additionalPanelsInput.click();
    await this.additionalPanelsInput.pressSequentially(name);
    await this.page.getByRole("option", { name }).click();
  }

  async setRating(value: string) {
    await this.ratingInput.selectOption(value);
  }

  async setCurrentDiagnostic(value: boolean) {
    await this.currentDiagnosticInput.setChecked(value);
  }

  async setComments(value: string) {
    await this.commentsInput.pressSequentially(value);
  }

  async fill(data: NewPanelGene) {
    await this.setGeneSymbol(data.symbol);

    if (data.sources) {
      for (const sourceName of data.sources) {
        await this.addSource(sourceName);
      }
    }
    if (data.modeOfPathogenicity) {
      await this.setModeOfPathogenicity(data.modeOfPathogenicity);
    }
    if (data.modeOfInheritance) {
      await this.setModeOfInheritance(data.modeOfInheritance);
    }
    if (data.penetrance) {
      await this.setPenetrance(data.penetrance);
    }
    if (data.publications) {
      await this.setPublications(data.publications);
    }
    if (data.phenotypes) {
      await this.setPhenotypes(data.phenotypes);
    }
    if (data.tags) {
      for (const tagName of data.tags) {
        await this.addTag(tagName);
      }
    }
    if (data.transcripts) {
      await this.setTranscripts(data.transcripts);
    }
    if (data.additionalPanels) {
      for (const panelName of data.additionalPanels) {
        await this.addAdditionalPanel(panelName);
      }
    }
    if (data.rating) {
      await this.setRating(data.rating);
    }
    if (data.currentDiagnostic) {
      await this.setCurrentDiagnostic(data.currentDiagnostic);
    }
    if (data.comments) {
      await this.setComments(data.comments);
    }
  }

  async submit() {
    await this.submitButton.click();
  }
}
