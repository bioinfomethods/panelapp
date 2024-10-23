import { expect, Page } from "@playwright/test";

export class LoginPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto("/accounts/login/?next=/");
  }

  async login(username: string, password: string) {
    const form = new LoginForm(this.page);
    await form.fill(username, password);
    await form.submit();
    await expect(
      this.page.getByRole("link", { name: "Log out" })
    ).toBeVisible();
  }
}

export class LoginForm {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  get usernameInput() {
    return this.page.getByPlaceholder("Username");
  }

  get passwordInput() {
    return this.page.getByPlaceholder("Password");
  }

  get submitButton() {
    return this.page.getByRole("button", { name: "Log in" });
  }

  async fill(username: string, password: string) {
    await this.usernameInput.click();
    await this.usernameInput.fill(username);
    await this.passwordInput.click();
    await this.passwordInput.fill(password);
  }

  async submit() {
    await this.submitButton.click();
  }
}
