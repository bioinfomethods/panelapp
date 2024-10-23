Feature: Manage panels

  Scenario: Create panel
    Given I log in as "TEST_Curator"
    When I create a panel
      | ID | Level4                               | Status   |
      | 1  | 0238047d-eb68-470d-9fba-330787d8cdd6 | internal |
    Then I see panels
      | Level4                               | Version |
      | 0238047d-eb68-470d-9fba-330787d8cdd6 | 0.0     |

  Scenario: Add gene to panel
    Given there are panels
      | ID | Level4                               | Status   | Version |
      | 1  | 93992918-79d1-4e54-91f4-381631d0a12c | internal | 0.0     |
    And I log in as "TEST_Curator"
    When I add a gene to the panel
      | ID | Panel ID | Gene symbol | Sources                   | Mode of inheritance | Rating                  |
      | 1  | 1        | BRCA1       | Emory Genetics Laboratory | MITOCHONDRIAL       | Red List (low evidence) |
    Then I see panel genes
      | Panel ID | Gene symbol |
      | 1        | BRCA1       |
    And I see panels
      | Level4                               | Version |
      | 93992918-79d1-4e54-91f4-381631d0a12c | 0.1     |

  Scenario: Super panels only contain component panel entities
    Given there are panels
      | ID | Level4                               | Status |
      | 1  | 95e1eda0-207e-4b8a-b019-98e3933a6f9c | public |
      | 2  | ead7c2a6-34a2-4759-8949-87c5effd4fe6 | public |
    And there are panel genes
      | ID | Panel ID | Gene symbol | Sources                   | Mode of inheritance                     | Rating                  |
      | 1  | 1        | BRCA1       | Emory Genetics Laboratory | MITOCHONDRIAL                           | Red List (low evidence) |
      | 2  | 2        | BRCA1       | Emory Genetics Laboratory | BIALLELIC, autosomal or pseudoautosomal | Red List (low evidence) |
    And I log in as "TEST_Curator"
    # Make Panel 1 into a Super Panel
    When I edit the panel
      | Panel ID | Child panels                         |
      | 1        | ead7c2a6-34a2-4759-8949-87c5effd4fe6 |
    Then I see panel genes
      | Panel ID | Gene symbol | Mode of inheritance                     |
      | 2        | BRCA1       | BIALLELIC, autosomal or pseudoautosomal |
    And I do not see panel genes
      | Panel ID | Gene symbol | Mode of inheritance |
      | 1        | BRCA1       | MITOCHONDRIAL       |
