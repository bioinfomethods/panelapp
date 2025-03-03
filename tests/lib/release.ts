import { Page } from "@playwright/test";
import { v4 as uuidv4 } from "uuid";
import { Identifiable, Provenance, TestIdentifiable } from "./types";

export interface NewRelease extends TestIdentifiable, Provenance {
  name: string;
  promotionComment?: string;
}

export interface Release extends NewRelease, Identifiable {}

export const parseNewRelease = (data: Record<string, string>): NewRelease => {
  return {
    testId: data["ID"],
    createdBy: data["User"] || "admin",
    name: data["Name"] ? data["Name"] : uuidv4(),
    promotionComment: data["Promotion Comment"],
  };
};

abstract class ReleaseForm {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  get nameInput() {
    return this.page.getByPlaceholder("Name");
  }

  get promotionCommentInput() {
    return this.page.getByPlaceholder("Promotion comment");
  }

  get submitButton() {
    return this.page.getByRole("button", { name: "Create" });
  }

  async setName(value: string) {
    await this.nameInput.fill(value);
  }

  async setPromotionComment(value: string) {
    await this.promotionCommentInput.fill(value);
  }

  async fill(data: { name: string; promotionComment?: string }) {
    await this.setName(data.name);
    if (data.promotionComment) {
      await this.setPromotionComment(data.promotionComment);
    }
  }

  async submit() {
    await this.submitButton.click();
  }
}

export class NewReleaseForm extends ReleaseForm {
  get submitButton() {
    return this.page.getByRole("button", { name: "Create" });
  }

  async submit() {
    await this.submitButton.click();
  }
}

export class EditReleaseForm extends ReleaseForm {
  get submitButton() {
    return this.page.getByRole("button", { name: "Submit" });
  }

  async submit() {
    await this.submitButton.click();
  }
}

export class ReleaseListPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto("/releases/");
  }

  async search(term: string) {
    await this.page.getByPlaceholder("Search").fill(term);
  }

  async find({
    search,
    deployment,
  }: {
    search?: string;
    deployment?: string[];
  }) {
    if (search) {
      await this.search(search);
    }

    if (deployment) {
      for (const status of deployment) {
        await this.page.getByLabel(status).check();
      }
    }
  }
}
