import { expect, Page } from "@playwright/test";
import { Select2Multiple } from "../lib/select2";

export class ReviewFeedback {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  get tagsInput() {
    return new Select2Multiple(this.page, "Tags");
  }

  get clearTagsButton() {
    return this.page.locator("#part-tags").getByTitle("Remove all items");
  }

  get saveTagsButton() {
    return this.page.getByRole("button", { name: "Save changes" });
  }

  get editRatingButton() {
    return this.page
      .locator("#part-rating")
      .getByRole("link", { name: "Edit" });
  }

  get ratingInput() {
    return this.page.getByLabel("Status");
  }

  get ratingCommentInput() {
    return this.page
      .getByRole("cell", { name: "Status" })
      .getByPlaceholder("Comment");
  }

  get updateRatingButton() {
    return this.page
      .locator("#part-rating")
      .getByRole("button", { name: "Update" });
  }

  get cancelRatingButton() {
    return this.page
      .locator("#part-rating")
      .getByRole("link", { name: "Cancel" });
  }

  get editMOIButton() {
    return this.page.locator("#part-moi").getByRole("link", { name: "Edit" });
  }

  get moiInput() {
    return this.page.locator("#part-moi").getByRole("combobox");
  }

  get moiCommentInput() {
    return this.page.locator("#part-moi").getByPlaceholder("Comment");
  }

  get updateMOIButton() {
    return this.page
      .locator("#part-moi")
      .getByRole("button", { name: "Update" });
  }

  get cancelMOIButton() {
    return this.page.locator("#part-moi").getByRole("link", { name: "Cancel" });
  }

  get editMOPButton() {
    return this.page.locator("#part-mop").getByRole("link", { name: "Edit" });
  }

  get mopInput() {
    return this.page.locator("#part-mop").getByRole("combobox");
  }

  get mopCommentInput() {
    return this.page.locator("#part-mop").getByPlaceholder("Comment");
  }

  get updateMOPButton() {
    return this.page
      .locator("#part-mop")
      .getByRole("button", { name: "Update" });
  }

  get cancelMOPButton() {
    return this.page.locator("#part-mop").getByRole("link", { name: "Cancel" });
  }

  get editPublicationsButton() {
    return this.page
      .locator("#part-publications")
      .getByRole("link", { name: "Edit" });
  }

  get publicationsInput() {
    return this.page
      .locator("#part-publications")
      .getByPlaceholder("Publications (separate using");
  }

  get publicationsCommentInput() {
    return this.page.locator("#part-publications").getByPlaceholder("Comment");
  }

  get updatePublicationsButton() {
    return this.page
      .locator("#part-publications")
      .getByRole("button", { name: "Save publications" });
  }

  get cancelPublicationsButton() {
    return this.page
      .locator("#part-publications")
      .getByRole("link", { name: "Cancel" });
  }

  get editPhenotypesButton() {
    return this.page
      .locator("#part-phenotypes")
      .getByRole("link", { name: "Edit" });
  }

  get phenotypesInput() {
    return this.page
      .locator("#part-phenotypes")
      .getByPlaceholder("Phenotypes (separate using");
  }

  get phenotypesCommentInput() {
    return this.page.locator("#part-phenotypes").getByPlaceholder("Comment");
  }

  get updatePhenotypesButton() {
    return this.page
      .locator("#part-phenotypes")
      .getByRole("button", { name: "Save phenotypes" });
  }

  get cancelPhenotypesButton() {
    return this.page
      .locator("#part-phenotypes")
      .getByRole("link", { name: "Cancel" });
  }

  get markReadyButton() {
    return this.page.getByRole("button", { name: "Mark as ready" });
  }

  get markNotReadyButton() {
    return this.page.getByRole("button", { name: "Mark as not ready" });
  }

  get markReadyCommentInput() {
    return this.page.getByPlaceholder("Comment (eg What decisions");
  }

  async setTags(tags: string[]) {
    if (await this.clearTagsButton.isVisible()) {
      await this.clearTagsButton.click();
    }
    for (const tag of tags) {
      await this.tagsInput.select(tag);
    }
    await this.saveTagsButton.click();

    await expect(this.page.getByText(/Saved at \d\d:\d\d:\d\d/)).toBeVisible();
  }

  async setRating(rating: string, comment?: string) {
    await this.editRatingButton.click();
    await this.ratingInput.selectOption(rating);
    if (comment) {
      await this.ratingCommentInput.fill(comment);
    }
    await this.updateRatingButton.click();

    await expect(this.editRatingButton).toBeVisible();
  }

  async setModeOfInheritance(moi: string, comment?: string) {
    await this.editMOIButton.click();
    await this.moiInput.selectOption(moi);
    if (comment) {
      await this.moiCommentInput.fill(comment);
    }
    await this.updateMOIButton.click();

    await expect(this.editMOIButton).toBeVisible();
  }

  async setModeOfPathogenicity(mop: string, comment?: string) {
    await this.editMOPButton.click();
    await this.mopInput.selectOption(mop);
    if (comment) {
      await this.mopCommentInput.fill(comment);
    }
    await this.updateMOPButton.click();

    await expect(this.editMOPButton).toBeVisible();
  }

  async setPublications(publications: string[], comment?: string) {
    await this.editPublicationsButton.click();
    await this.publicationsInput.fill(publications.join(";"));
    if (comment) {
      await this.publicationsCommentInput.fill(comment);
    }
    await this.updatePublicationsButton.click();

    await expect(this.editPublicationsButton).toBeVisible();
  }

  async setPhenotypes(phenotypes: string[], comment?: string) {
    await this.editPhenotypesButton.click();
    await this.phenotypesInput.fill(phenotypes.join(";"));
    if (comment) {
      await this.phenotypesCommentInput.fill(comment);
    }
    await this.updatePhenotypesButton.click();

    await expect(this.editPhenotypesButton).toBeVisible();
  }

  async markReady(comment?: string) {
    if (comment) {
      await this.markReadyCommentInput.fill(comment);
    }
    await this.markReadyButton.click();

    await expect(this.markNotReadyButton).toBeVisible();
  }

  async markNotReady() {
    await this.markNotReadyButton.click();

    await expect(this.markReadyButton).toBeVisible();
  }
}
