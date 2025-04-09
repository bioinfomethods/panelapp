import { Page } from "@playwright/test";
import { TestIdentifiable } from "./types";

export interface NewPanelStr extends TestIdentifiable {
  panelTestId: string;
  name: string;
  chromosome: string;
  position38Start: number;
  position38End: number;
  repeatedSequence: string;
  normal: number;
  pathogenic: number;
  sources: string[];
  modeOfInheritance: string;
  position37Start?: number;
  position37End?: number;
  symbol?: string;
  penetrance?: string;
  publications?: string;
  phenotypes?: string;
  tags?: string[];
  additionalPanels?: string[];
  rating?: string;
  currentDiagnostic?: boolean;
  comments?: string;
}

export interface PanelStr extends NewPanelStr {}

export const parseNewPanelStr = (data: Record<string, string>): NewPanelStr => {
  return {
    testId: data["ID"],
    panelTestId: data["Panel ID"],
    name: data["Name"],
    chromosome: data["Chromosome"] ? data["Chromosome"] : "1",
    position38Start: data["Pos 38 Start"]
      ? Number.parseInt(data["Pos 38 Start"])
      : 1,
    position38End: data["Pos 38 End"] ? Number.parseInt(data["Pos 38 End"]) : 2,
    repeatedSequence: data["Sequence"],
    normal: data["Normal"] ? Number.parseInt(data["Normal"]) : 10,
    pathogenic: data["Pathogenic"] ? Number.parseInt(data["Pathogenic"]) : 20,
    sources: data["Sources"].split(",").filter((x) => x),
    modeOfInheritance: data["Mode of inheritance"],
    position37Start: data["Pos 37 Start"]
      ? Number.parseInt(data["Pos 37 Start"])
      : 1,
    position37End: data["Pos 37 End"] ? Number.parseInt(data["Pos 37 End"]) : 2,
    symbol: data["Gene symbol"],
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

export class AddStrForm {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  get nameInput() {
    return this.page.getByPlaceholder("Name");
  }

  get chromosomeInput() {
    return this.page.getByLabel("Chromosome:");
  }

  get position37StartInput() {
    return this.page.getByPlaceholder("Position start (GRCh37)");
  }

  get position37EndInput() {
    return this.page.getByPlaceholder("Position end (GRCh37)");
  }

  get position38StartInput() {
    return this.page.getByPlaceholder("Position start (GRCh38)");
  }

  get position38EndInput() {
    return this.page.getByPlaceholder("Position end (GRCh38)");
  }

  get repeatedSequenceInput() {
    return this.page.getByPlaceholder("Repeated sequence");
  }

  get normalInput() {
    return this.page.getByPlaceholder("Normal");
  }

  get pathogenicInput() {
    return this.page.getByPlaceholder("Pathogenic");
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
    return this.page.getByRole("button", { name: "Add STR" });
  }

  async setName(name: string) {
    await this.nameInput.fill(name);
  }

  async setChromosome(chromosome: string) {
    await this.chromosomeInput.selectOption(chromosome);
  }

  async setPosition38Start(value: number) {
    await this.position38StartInput.fill(value.toString());
  }

  async setPosition38End(value: number) {
    await this.position38EndInput.fill(value.toString());
  }

  async setRepeatedSequence(value: string) {
    await this.repeatedSequenceInput.fill(value);
  }

  async setNormal(value: number) {
    await this.normalInput.fill(value.toString());
  }

  async setPathogenic(value: number) {
    await this.pathogenicInput.fill(value.toString());
  }

  async setPosition37Start(value: number) {
    await this.position37StartInput.fill(value.toString());
  }

  async setPosition37End(value: number) {
    await this.position37EndInput.fill(value.toString());
  }

  async setGeneSymbol(name: string) {
    await this.geneSymbolInput.click();
    await this.page.getByRole("searchbox").nth(3).pressSequentially(name);
    await this.page.getByRole("option", { name }).click();
  }

  async addSource(name: string) {
    await this.sourceInput.pressSequentially(name);
    await this.page.getByRole("option", { name }).click();
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

  async fill(data: NewPanelStr) {
    await this.setName(data.name);

    if (data.chromosome) {
      await this.setChromosome(data.chromosome);
    }

    if (data.position38Start) {
      await this.setPosition38Start(data.position38Start);
    }

    if (data.position38End) {
      await this.setPosition38End(data.position38End);
    }

    if (data.position37Start) {
      await this.setPosition37Start(data.position37Start);
    }

    if (data.position37End) {
      await this.setPosition37End(data.position37End);
    }

    if (data.repeatedSequence) {
      await this.setRepeatedSequence(data.repeatedSequence);
    }

    if (data.normal) {
      await this.setNormal(data.normal);
    }

    if (data.pathogenic) {
      await this.setPathogenic(data.pathogenic);
    }

    if (data.sources) {
      for (const sourceName of data.sources) {
        await this.addSource(sourceName);
      }
    }
    if (data.modeOfInheritance) {
      await this.setModeOfInheritance(data.modeOfInheritance);
    }

    if (data.symbol) {
      await this.setGeneSymbol(data.symbol);
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
