import { Page } from "@playwright/test";
import { Identifiable, Provenance, TestIdentifiable } from "./types";

export interface NewStrReview extends TestIdentifiable, Provenance {
  panelStrTestId: string;
  rating?: string;
  modeOfInheritance?: string;
  publications?: string;
  phenotypes?: string;
  currentDiagnostic?: boolean;
  comments?: string;
}

export interface StrReview extends NewStrReview, Identifiable {}

export const parseNewStrReview = (
  data: Record<string, string>
): NewStrReview => {
  return {
    testId: data["ID"],
    panelStrTestId: data["Panel Str ID"],
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

export class ReviewStrForm {
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

export interface NewStrReviewComment extends TestIdentifiable, Provenance {
  reviewTestId: string;
  content: string;
}

export interface StrReviewComment extends NewStrReviewComment, Identifiable {}

export const parseNewStrReviewComment = (
  data: Record<string, string>
): NewStrReviewComment => {
  return {
    testId: data["ID"],
    reviewTestId: data["Str Review ID"],
    content: data["Content"],
    createdBy: data["User"] || "admin",
  };
};
