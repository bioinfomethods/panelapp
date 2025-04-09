import { Page } from "@playwright/test";
import { TestIdentifiable } from "./types";

export interface NewPanelRegion extends TestIdentifiable {
  panelTestId: string;
  name: string;
  chromosome: string;
  position38Start: number;
  position38End: number;
  haploinsufficiencyScore: string;
  triplosensitivityScore: string;
  requiredOverlap: number;
  sources: string[];
  modeOfInheritance: string;
  verboseName?: string;
  position37Start?: number;
  position37End?: number;
  symbol?: string;
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

export interface PanelRegion extends NewPanelRegion {}

export const parseNewPanelRegion = (
  data: Record<string, string>
): NewPanelRegion => {
  return {
    testId: data["ID"],
    panelTestId: data["Panel ID"],
    name: data["Name"],
    chromosome: data["Chromosome"] ? data["Chromosome"] : "1",
    position38Start: data["Pos 38 Start"]
      ? Number.parseInt(data["Pos 38 Start"])
      : 1,
    position38End: data["Pos 38 End"] ? Number.parseInt(data["Pos 38 End"]) : 2,
    haploinsufficiencyScore: data["Haplo"]
      ? data["Haplo"]
      : "No evidence to suggest that dosage sensitivity is associated with clinical phenotype",
    triplosensitivityScore: data["Triplo"]
      ? data["Triplo"]
      : "No evidence to suggest that dosage sensitivity is associated with clinical phenotype",
    requiredOverlap: data["Overlap"] ? Number.parseInt(data["Overlap"]) : 10,
    symbol: data["Gene symbol"],
    sources: data["Sources"].split(",").filter((x) => x),
    modeOfInheritance: data["Mode of inheritance"],
    verboseName: data["Verbose Name"],
    position37Start: data["Pos 37 Start"]
      ? Number.parseInt(data["Pos 37 Start"])
      : 1,
    position37End: data["Pos 37 End"] ? Number.parseInt(data["Pos 37 End"]) : 2,
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

export class AddRegionForm {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  get nameInput() {
    return this.page.getByPlaceholder("Name", { exact: true });
  }

  get verboseNameInput() {
    return this.page.getByPlaceholder("Verbose name");
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

  get haploinsufficiencyScoreInput() {
    return this.page.getByLabel("Haploinsufficiency score:");
  }

  get triplosensitivityScoreInput() {
    return this.page.getByLabel("Triplosensitivity score:");
  }

  get requiredOverlapInput() {
    return this.page.getByPlaceholder("Required overlap percentage");
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
    return this.page.getByRole("button", { name: "Add Region" });
  }

  async setName(name: string) {
    await this.nameInput.fill(name);
  }

  async setVerboseName(name: string) {
    await this.verboseNameInput.fill(name);
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

  async setPosition37Start(value: number) {
    await this.position37StartInput.fill(value.toString());
  }

  async setPosition37End(value: number) {
    await this.position37EndInput.fill(value.toString());
  }

  async setHaploinsufficiencyScore(value: string) {
    await this.haploinsufficiencyScoreInput.selectOption(value);
  }

  async setTriplosensitivityScore(value: string) {
    await this.triplosensitivityScoreInput.selectOption(value);
  }

  async setRequiredOverlap(value: number) {
    await this.requiredOverlapInput.fill(value.toString());
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

  async fill(data: NewPanelRegion) {
    await this.setName(data.name);

    if (data.verboseName) {
      await this.setVerboseName(data.verboseName);
    }

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

    if (data.haploinsufficiencyScore) {
      await this.setHaploinsufficiencyScore(data.haploinsufficiencyScore);
    }

    if (data.triplosensitivityScore) {
      await this.setTriplosensitivityScore(data.triplosensitivityScore);
    }

    if (data.requiredOverlap) {
      await this.setRequiredOverlap(data.requiredOverlap);
    }

    if (data.symbol) {
      await this.setGeneSymbol(data.symbol);
    }
    if (data.sources) {
      for (const sourceName of data.sources) {
        await this.addSource(sourceName);
      }
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
