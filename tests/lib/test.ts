import { test as base } from "playwright-bdd";
import { Pages, Panels } from "./panels";

interface Account {
  username: string;
  password: string;
  firstName: string;
  lastName: string;
}

interface Fixtures {
  pages: Pages;
  panels: Panels;
  accounts: Map<string, Account>;
}

// Fixtures: https://playwright.dev/docs/test-fixtures#creating-a-fixture
const fixtures = {
  pages: async ({ browser }, use) => {
    const pages = new Pages(browser);
    await use(pages);
    await pages.dispose();
  },
  panels: async ({ pages }, use) => {
    const panels = new Panels(pages);
    await use(panels);
    await panels.dispose();
  },
  accounts: async ({}, use) => {
    await use(
      new Map([
        [
          "admin",
          {
            username: "admin",
            password: "changeme",
            firstName: "",
            lastName: "",
          },
        ],
        [
          "TEST_Curator",
          {
            username: "TEST_Curator",
            password: "changeme",
            firstName: "Curator",
            lastName: "Test",
          },
        ],
        [
          "TEST_Reviewer",
          {
            username: "TEST_Reviewer",
            password: "changeme",
            firstName: "Reviewer",
            lastName: "Test",
          },
        ],
      ])
    );
  },
};

export const test = base.extend<Fixtures>(fixtures);
