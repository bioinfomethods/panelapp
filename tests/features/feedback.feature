Feature: Review feedback
  Background:
    Given there are panels
      | ID | Status |
      | 1  | public |
    And I log in as "TEST_Curator"

  Scenario: Gene
    Given there are panel genes
      | ID | Panel ID | Gene symbol | Sources                   | Mode of inheritance | Rating                  |
      | 1  | 1        | BRCA1       | Emory Genetics Laboratory | Unknown             | Red List (low evidence) |
    And there are gene reviews
      | ID | Panel Gene ID | Rating                     | User          |
      | 1  | 1             | Green List (high evidence) | TEST_Reviewer |
    When I review feedback for gene "1"
      | Property              | Value                      | Comment              |
      | Rating                | Green List (high evidence) | Rating comment       |
      | Mode of inheritance   | MITOCHONDRIAL              | MOI comment          |
      | Mode of pathogenicity | Other                      | MOP comment          |
      | Publications          | 0923;1874                  | Publications comment |
      | Phenotypes            | phenotype1;phenotype2      | Phenotypes comment   |
      | Ready                 | true                       | Ready comment        |
      | Tags                  | test01,test02              |                      |
    Then I see panel genes
      | Panel ID | Gene symbol | Tags          | Rating                     | Mode of inheritance | Mode of pathogenicity | Publications | Phenotypes            | Ready |
      | 1        | BRCA1       | test01,test02 | Green List (high evidence) | MITOCHONDRIAL       | Other                 | 0923;1874    | phenotype1;phenotype2 | true  |

  Scenario: STR
    Given there are panel strs
      | ID | Panel ID | Name   | Sources                   | Mode of inheritance | Rating                  | Sequence |
      | 1  | 1        | AR_CAG | Emory Genetics Laboratory | Unknown             | Red List (low evidence) | CAG      |
    And there are str reviews
      | ID | Panel Str ID | Rating                     | User          |
      | 1  | 1            | Green List (high evidence) | TEST_Reviewer |
    When I review feedback for str "1"
      | Property            | Value                      | Comment              |
      | Rating              | Green List (high evidence) | Rating comment       |
      | Mode of inheritance | MITOCHONDRIAL              | MOI comment          |
      | Publications        | 0923;1874                  | Publications comment |
      | Phenotypes          | phenotype1;phenotype2      | Phenotypes comment   |
      | Ready               | true                       | Ready comment        |
      | Tags                | test01,test02              |                      |
    Then I see panel strs
      | Panel ID | Name   | Tags          | Rating                     | Mode of inheritance | Publications | Phenotypes            | Ready |
      | 1        | AR_CAG | test01,test02 | Green List (high evidence) | MITOCHONDRIAL       | 0923;1874    | phenotype1;phenotype2 | true  |

  Scenario: Region
    Given there are panel regions
      | ID | Panel ID | Name      | Sources                   | Mode of inheritance | Rating                  |
      | 1  | 1        | ISCA_0001 | Emory Genetics Laboratory | Unknown             | Red List (low evidence) |
    And there are region reviews
      | ID | Panel Region ID | Rating                     | User          |
      | 1  | 1               | Green List (high evidence) | TEST_Reviewer |
    When I review feedback for region "1"
      | Property            | Value                      | Comment              |
      | Rating              | Green List (high evidence) | Rating comment       |
      | Mode of inheritance | MITOCHONDRIAL              | MOI comment          |
      | Publications        | 0923;1874                  | Publications comment |
      | Phenotypes          | phenotype1;phenotype2      | Phenotypes comment   |
      | Ready               | true                       | Ready comment        |
      | Tags                | test01,test02              |                      |
    Then I see panel regions
      | Panel ID | Name      | Tags          | Rating                     | Mode of inheritance | Publications | Phenotypes            | Ready |
      | 1        | ISCA_0001 | test01,test02 | Green List (high evidence) | MITOCHONDRIAL       | 0923;1874    | phenotype1;phenotype2 | true  |
