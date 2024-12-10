import { Page } from "@playwright/test";
import { Identifiable, Provenance, TestIdentifiable } from "./types";

export interface NewRegionReview extends TestIdentifiable, Provenance {
  panelRegionTestId: string;
  rating?: string;
  modeOfInheritance?: string;
  publications?: string;
  phenotypes?: string;
  currentDiagnostic?: boolean;
  comments?: string;
}

export interface RegionReview extends NewRegionReview, Identifiable {}

export const parseNewRegionReview = (
  data: Record<string, string>
): NewRegionReview => {
  return {
    testId: data["ID"],
    panelRegionTestId: data["Panel Region ID"],
    rating: data["Rating"],
    modeOfInheritance: data["Mode of inheritance"],
    publications: data["Publications"],
    phenotypes: data["Phenotypes"],
    currentDiagnostic:
      data["Current diagnostic"] !== undefined
        ? data["Current diagnostic"].toLowerCase() === "yes"
        : undefined,
    comments: data["Comments"],
    createdBy: data["User"] || "admin",
  };
};

export class ReviewRegionForm {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  get ratingInput() {
    return this.page.getByLabel("Rating");
  }

  get modeOfInheritanceInput() {
    return this.page.getByLabel("Mode of inheritance:");
  }

  get publicationsInput() {
    return this.page.getByLabel("Publications (PMID: 1234;4321");
  }

  get phenotypesInput() {
    return this.page.getByLabel("Phenotypes (separate using a");
  }

  get currentDiagnosticInput() {
    return this.page.getByLabel("Current diagnostic:");
  }

  get commentsInput() {
    return this.page.getByPlaceholder("Comments");
  }

  get submitButton() {
    return this.page.getByRole("button", { name: "Submit review" });
  }

  async setRating(value: string) {
    await this.ratingInput.selectOption(value);
  }

  async setModeOfInheritance(value: string) {
    await this.modeOfInheritanceInput.selectOption(value);
  }

  async setPublications(value: string) {
    await this.publicationsInput.clear();
    await this.publicationsInput.pressSequentially(value);
  }

  async setPhenotypes(value: string) {
    await this.phenotypesInput.clear();
    await this.phenotypesInput.pressSequentially(value);
  }

  async setCurrentDiagnostic(value: boolean) {
    await this.currentDiagnosticInput.setChecked(value);
  }

  async setComments(value: string) {
    await this.commentsInput.pressSequentially(value);
  }

  async fill(data: {
    rating?: string;
    modeOfInheritance?: string;
    publications?: string;
    phenotypes?: string;
    currentDiagnostic?: boolean;
    comments?: string;
  }) {
    if (data.modeOfInheritance) {
      await this.setModeOfInheritance(data.modeOfInheritance);
    }
    if (data.publications) {
      await this.setPublications(data.publications);
    }
    if (data.phenotypes) {
      await this.setPhenotypes(data.phenotypes);
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

export interface NewRegionReviewComment extends TestIdentifiable, Provenance {
  reviewTestId: string;
  content: string;
}

export interface RegionReviewComment
  extends NewRegionReviewComment,
    Identifiable {}

export const parseNewRegionReviewComment = (
  data: Record<string, string>
): NewRegionReviewComment => {
  return {
    testId: data["ID"],
    reviewTestId: data["Region Review ID"],
    content: data["Content"],
    createdBy: data["User"] || "admin",
  };
};
