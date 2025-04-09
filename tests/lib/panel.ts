import { Page } from "@playwright/test";
import { v4 as uuidv4 } from "uuid";
import { Select2Multiple } from "./select2";
import { Identifiable, Provenance, TestIdentifiable } from "./types";

export interface NewPanel extends TestIdentifiable, Provenance {
  level4: string;
  description: string;
  level2?: string;
  level3?: string;
  omim?: string;
  orphanet?: string;
  hpo?: string;
  oldPanels?: string;
  panelTypes?: string[];
  signedOffVersion?: string;
  signedOffDate?: string;
  childPanels?: string[];
  status?: string;
  version?: string;
  comment?: string;
}

export interface Panel extends NewPanel, Identifiable {}

export const parseNewPanel = (data: Record<string, string>): NewPanel => {
  return {
    testId: data["ID"],
    level2: data["Level2"],
    level3: data["Level3"],
    level4: data["Level4"] ? data["Level4"] : uuidv4(),
    description: data["Description"] ? data["Description"] : uuidv4(),
    omim: data["Omim"],
    orphanet: data["Orphanet"],
    hpo: data["Hpo"],
    oldPanels: data["Old panels"],
    panelTypes: data["Panel types"]
      ? data["Panel types"]
          .split(",")
          // remove empty elements
          .filter((x) => x)
      : undefined,
    signedOffVersion: data["Signed off version"],
    signedOffDate: data["Signed off date"],
    childPanels: data["Child panels"]
      ? data["Child panels"]
          .split(",")
          // remove empty elements
          .filter((x) => x)
      : undefined,
    status: data["Status"],
    version: data["Version"],
    comment: data["Comment"],
    createdBy: data["User"] || "admin",
  };
};

export interface EditPanel extends TestIdentifiable {
  level4?: string;
  description?: string;
  level2?: string;
  level3?: string;
  omim?: string;
  orphanet?: string;
  hpo?: string;
  oldPanels?: string;
  panelTypes?: string[];
  signedOffVersion?: string;
  signedOffDate?: string;
  childPanels?: string[];
  status?: string;
}

export const parseEditPanel = (data: Record<string, string>): EditPanel => {
  return {
    testId: data["ID"],
    level2: data["Level2"],
    level3: data["Level3"],
    level4: data["Level4"],
    description: data["Description"],
    omim: data["Omim"],
    orphanet: data["Orphanet"],
    hpo: data["Hpo"],
    oldPanels: data["Old panels"],
    panelTypes: data["Panel types"]
      ? data["Panel types"]
          .split(",")
          // remove empty elements
          .filter((x) => x)
      : undefined,
    signedOffVersion: data["Signed off version"],
    signedOffDate: data["Signed off date"],
    childPanels: data["Child panels"]
      ? data["Child panels"]
          .split(",")
          // remove empty elements
          .filter((x) => x)
      : undefined,
    status: data["Status"],
  };
};

abstract class PanelForm {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  get level2Input() {
    return this.page.getByPlaceholder("Level2");
  }

  get level3Input() {
    return this.page.getByPlaceholder("Level3");
  }

  get level4Input() {
    return this.page.getByPlaceholder("Level4");
  }

  get descriptionInput() {
    return this.page.getByPlaceholder("Description");
  }

  get omimInput() {
    return this.page.getByPlaceholder("Omim");
  }

  get orphanetInput() {
    return this.page.getByPlaceholder("Orphanet");
  }

  get hpoInput() {
    return this.page.getByPlaceholder("Hpo");
  }

  get oldPanelsInput() {
    return this.page.getByPlaceholder("Old panels");
  }

  get panelTypesInput() {
    return new Select2Multiple(this.page, "Panel Types");
  }

  get childPanelsInput() {
    return new Select2Multiple(this.page, "Child Panels");
  }

  get signedOffVersionInput() {
    return this.page.getByPlaceholder("Signed Off Version");
  }

  get signedOffDateInput() {
    return this.page.getByPlaceholder("Signed Off Date in format dd/");
  }

  get statusInput() {
    return this.page.getByLabel("Status");
  }

  async setLevel2(value: string) {
    await this.level2Input.clear();
    await this.level2Input.pressSequentially(value);
  }

  async setLevel3(value: string) {
    await this.level3Input.clear();
    await this.level3Input.pressSequentially(value);
  }

  async setLevel4(value: string) {
    await this.level4Input.clear();
    await this.level4Input.pressSequentially(value);
  }

  async setDescription(value: string) {
    await this.descriptionInput.clear();
    await this.descriptionInput.pressSequentially(value);
  }

  async setOmim(value: string) {
    await this.omimInput.clear();
    await this.omimInput.pressSequentially(value);
  }

  async setOrphanet(value: string) {
    await this.orphanetInput.clear();
    await this.orphanetInput.pressSequentially(value);
  }

  async setHpo(value: string) {
    await this.hpoInput.clear();
    await this.hpoInput.pressSequentially(value);
  }

  async setOldPanels(value: string) {
    await this.oldPanelsInput.clear();
    await this.oldPanelsInput.pressSequentially(value);
  }

  async addPanelType(name: string) {
    await this.panelTypesInput.select(name);
  }

  async setSignedOffVersion(value: string) {
    await this.signedOffVersionInput.clear();
    await this.signedOffVersionInput.fill(value);
  }

  async setSignedOffDate(value: string) {
    await this.signedOffDateInput.clear();
    await this.signedOffDateInput.fill(value);
  }

  async addChildPanel(name: string) {
    await this.childPanelsInput.select(name);
  }

  async setStatus(value: string) {
    await this.statusInput.selectOption(value);
  }
}

export class NewPanelForm extends PanelForm {
  get submitButton() {
    return this.page.getByRole("button", { name: "Submit" });
  }

  async fill(data: NewPanel) {
    await this.setLevel4(data.level4);
    await this.setDescription(data.description);
    if (data.level2) {
      await this.setLevel2(data.level2);
    }
    if (data.level3) {
      await this.setLevel3(data.level3);
    }
    if (data.omim) {
      await this.setOmim(data.omim);
    }
    if (data.orphanet) {
      await this.setOrphanet(data.orphanet);
    }
    if (data.hpo) {
      await this.setHpo(data.hpo);
    }
    if (data.oldPanels) {
      await this.setOldPanels(data.oldPanels);
    }
    if (data.panelTypes) {
      for (const panelTypeName of data.panelTypes) {
        await this.addPanelType(panelTypeName);
      }
    }
    if (data.signedOffVersion) {
      await this.setSignedOffVersion(data.signedOffVersion);
    }
    if (data.signedOffDate) {
      await this.setSignedOffDate(data.signedOffDate);
    }
    if (data.childPanels) {
      for (const childPanelName of data.childPanels) {
        await this.addChildPanel(childPanelName);
      }
    }
    if (data.status) {
      await this.setStatus(data.status);
    }
  }
  async submit() {
    await this.submitButton.click();
  }
}

export class EditPanelForm extends PanelForm {
  get submitButton() {
    return this.page.getByRole("button", { name: "Save" });
  }

  async fill(data: EditPanel) {
    if (data.level4) {
      await this.setLevel4(data.level4);
    }
    if (data.description) {
      await this.setDescription(data.description);
    }
    if (data.level2) {
      await this.setLevel2(data.level2);
    }
    if (data.level3) {
      await this.setLevel3(data.level3);
    }
    if (data.omim) {
      await this.setOmim(data.omim);
    }
    if (data.orphanet) {
      await this.setOrphanet(data.orphanet);
    }
    if (data.hpo) {
      await this.setHpo(data.hpo);
    }
    if (data.oldPanels) {
      await this.setOldPanels(data.oldPanels);
    }
    if (data.panelTypes) {
      for (const panelTypeName of data.panelTypes) {
        await this.addPanelType(panelTypeName);
      }
    }
    if (data.signedOffVersion) {
      await this.setSignedOffVersion(data.signedOffVersion);
    }
    if (data.signedOffDate) {
      await this.setSignedOffDate(data.signedOffDate);
    }
    if (data.childPanels) {
      for (const childPanelName of data.childPanels) {
        await this.addChildPanel(childPanelName);
      }
    }
    if (data.status) {
      await this.setStatus(data.status);
    }
  }

  async submit() {
    await this.submitButton.click();
  }
}
