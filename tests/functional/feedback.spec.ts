import { expect } from "@playwright/test";
import { v4 as uuidv4 } from "uuid";
import { test } from "../lib/test";
import { ReviewFeedback } from "../pages/review-feedback";

test.describe(() => {
  test.use({ storageState: "playwright/.auth/TEST_Curator.json" });

  test("review gene", async ({ page, panels }) => {
    const panelName = uuidv4();
    const panelId = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panelName,
      description: uuidv4(),
    });
    await panels.addPanelGene({
      testId: "1",
      panelTestId: "1",
      symbol: "BRCA1",
      sources: ["Emory Genetics Laboratory"],
      modeOfInheritance: "Unknown",
      rating: "Red List (low evidence)",
    });
    await panels.reviewGene({
      testId: "1",
      panelGeneTestId: "1",
      createdBy: "TEST_Reviewer",
    });

    await page.goto(`/panels/${panelId}/gene/BRCA1/#!review`);

    await expect(
      page.getByRole("heading", { name: "Review feedback" })
    ).toBeVisible();

    const feedback = new ReviewFeedback(page);
    await feedback.setRating("Green List (high evidence)", "Rating comment");
    await feedback.setModeOfInheritance("MITOCHONDRIAL", "MOI comment");
    await feedback.setModeOfPathogenicity("Other", "MOP comment");
    await feedback.setPublications(["0923", "1874"], "Publications comment");
    await feedback.setPhenotypes(
      ["phenotype1", "phenotype2"],
      "Phenotypes comment"
    );
    await feedback.markReady("Ready comment");
    await feedback.setTags(["test01", "test02"]);

    await page.goto("/panels/entities/BRCA1");

    await expect(page.locator("#table")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /Green BRCA1 in ${panelName} Version 0\\.6 Panel not approved review MITOCHONDRIAL Sources Expert Review Green Emory Genetics Laboratory Phenotypes phenotype1 phenotype2 Tags test01 test02/:
            - cell /Green BRCA1 in ${panelName} Version 0\\.6 Panel not approved/:
              - heading /Green BRCA1 in ${panelName}/ [level=5]:
                - link "BRCA1"
                - link /${panelName}/
              - paragraph: Version 0.6 Panel not approved
            - cell "review"
            - cell "MITOCHONDRIAL"
            - cell "Sources Expert Review Green Emory Genetics Laboratory Phenotypes phenotype1 phenotype2 Tags test01 test02":
              - heading "Sources" [level=6]
              - list:
                - listitem: Expert Review Green
                - listitem: Emory Genetics Laboratory
              - heading "Phenotypes" [level=6]
              - list:
                - listitem: phenotype1
                - listitem: phenotype2
              - heading "Tags" [level=6]
              - list:
                - listitem: test01
                - listitem: test02
    `);
  });

  test("review str", async ({ page, panels }) => {
    const panelName = uuidv4();
    const panelId = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panelName,
      description: uuidv4(),
    });
    await panels.addPanelStr({
      testId: "1",
      panelTestId: "1",
      name: "AR_CAG",
      sources: ["Emory Genetics Laboratory"],
      modeOfInheritance: "Unknown",
      rating: "Red List (low evidence)",
      repeatedSequence: "CAG",
      chromosome: "1",
      position38Start: 1,
      position38End: 2,
      normal: 1,
      pathogenic: 2,
    });
    await panels.reviewStr({
      testId: "1",
      panelStrTestId: "1",
      createdBy: "TEST_Reviewer",
    });

    await page.goto(`/panels/${panelId}/str/AR_CAG/#!review`);

    await expect(
      page.getByRole("heading", { name: "Review feedback" })
    ).toBeVisible();

    const feedback = new ReviewFeedback(page);
    await feedback.setRating("Green List (high evidence)", "Rating comment");
    await feedback.setModeOfInheritance("MITOCHONDRIAL", "MOI comment");
    await feedback.setPublications(["0923", "1874"], "Publications comment");
    await feedback.setPhenotypes(
      ["phenotype1", "phenotype2"],
      "Phenotypes comment"
    );
    await feedback.markReady("Ready comment");
    await feedback.setTags(["test01", "test02"]);

    await page.goto("/panels/entities/AR_CAG");

    await expect(page.locator("#table")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /Green AR_CAG STR in ${panelName} Version 0\\.5 Panel not approved review MITOCHONDRIAL Sources Expert Review Green Emory Genetics Laboratory Phenotypes phenotype1 phenotype2 Tags test01 test02/:
            - cell /Green AR_CAG STR in ${panelName} Version 0\\.5 Panel not approved/:
              - heading /Green AR_CAG STR in ${panelName}/ [level=5]:
                - link "AR_CAG"
                - link /${panelName}/
              - paragraph: Version 0.5 Panel not approved
            - cell "review"
            - cell "MITOCHONDRIAL"
            - cell "Sources Expert Review Green Emory Genetics Laboratory Phenotypes phenotype1 phenotype2 Tags test01 test02":
              - heading "Sources" [level=6]
              - list:
                - listitem: Expert Review Green
                - listitem: Emory Genetics Laboratory
              - heading "Phenotypes" [level=6]
              - list:
                - listitem: phenotype1
                - listitem: phenotype2
              - heading "Tags" [level=6]
              - list:
                - listitem: test01
                - listitem: test02
    `);
  });

  test("review region", async ({ page, panels }) => {
    const panelName = uuidv4();
    const panelId = await panels.create({
      testId: "1",
      createdBy: "admin",
      level4: panelName,
      description: uuidv4(),
    });
    await panels.addPanelRegion({
      testId: "1",
      panelTestId: "1",
      name: "ISCA_0001",
      sources: ["Emory Genetics Laboratory"],
      modeOfInheritance: "Unknown",
      rating: "Red List (low evidence)",
      chromosome: "1",
      position38Start: 1,
      position38End: 2,
      haploinsufficiencyScore:
        "No evidence to suggest that dosage sensitivity is associated with clinical phenotype",
      triplosensitivityScore:
        "No evidence to suggest that dosage sensitivity is associated with clinical phenotype",
      requiredOverlap: 10,
    });
    await panels.reviewRegion({
      testId: "1",
      panelRegionTestId: "1",
      createdBy: "TEST_Reviewer",
    });

    await page.goto(`/panels/${panelId}/region/ISCA_0001/#!review`);

    await expect(
      page.getByRole("heading", { name: "Review feedback" })
    ).toBeVisible();

    const feedback = new ReviewFeedback(page);
    await feedback.setRating("Green List (high evidence)", "Rating comment");
    await feedback.setModeOfInheritance("MITOCHONDRIAL", "MOI comment");
    await feedback.setPublications(["0923", "1874"], "Publications comment");
    await feedback.setPhenotypes(
      ["phenotype1", "phenotype2"],
      "Phenotypes comment"
    );
    await feedback.markReady("Ready comment");
    await feedback.setTags(["test01", "test02"]);

    await page.goto("/panels/entities/ISCA_0001");

    await expect(page.locator("#table")).toMatchAriaSnapshot(`
      - table:
        - rowgroup:
          - row /Green ISCA_0001 Region in ${panelName} Version 0\\.5 Panel not approved review MITOCHONDRIAL Sources Expert Review Green Emory Genetics Laboratory Phenotypes phenotype1 phenotype2 Tags test01 test02/:
            - cell /Green ISCA_0001 Region in ${panelName} Version 0\\.5 Panel not approved/:
              - heading /Green ISCA_0001 Region in ${panelName}/ [level=5]:
                - link "ISCA_0001"
                - link /${panelName}/
              - paragraph: Version 0.5 Panel not approved
            - cell "review"
            - cell "MITOCHONDRIAL"
            - cell "Sources Expert Review Green Emory Genetics Laboratory Phenotypes phenotype1 phenotype2 Tags test01 test02":
              - heading "Sources" [level=6]
              - list:
                - listitem: Expert Review Green
                - listitem: Emory Genetics Laboratory
              - heading "Phenotypes" [level=6]
              - list:
                - listitem: phenotype1
                - listitem: phenotype2
              - heading "Tags" [level=6]
              - list:
                - listitem: test01
                - listitem: test02
    `);
  });
});
