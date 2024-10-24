Feature: Review genomic entities

  Background:
    Given there are panels
      | ID | Status |
      | 1  | public |
    And there are panel genes
      | ID | Panel ID | Gene symbol | Sources                   | Mode of inheritance | Rating                  |
      | 1  | 1        | BRCA1       | Emory Genetics Laboratory | MITOCHONDRIAL       | Red List (low evidence) |

  Scenario Outline: Review gene
    When I log in as "<username>"
    And I review the gene
      | ID | Panel Gene ID | Rating                     |
      | 1  | 1             | Green List (high evidence) |
    Then I see my review
    Examples:
      | username      |
      | TEST_Reviewer |
      | TEST_Curator  |

  Scenario Outline: Delete review
    Given there are gene reviews
      | ID | Panel Gene ID | Rating                     | User       |
      | 1  | 1             | Green List (high evidence) | <username> |
    When I log in as "<username>"
    And I delete the gene review
      | Gene Review ID |
      | 1              |
    Then I do not see my review
    Examples:
      | username      |
      | TEST_Reviewer |
      | TEST_Curator  |

  Scenario Outline: Create comment
    Given there are gene reviews
      | ID | Panel Gene ID | Rating                     | User       |
      | 1  | 1             | Green List (high evidence) | <username> |
    When I log in as "<username>"
    And I create a gene review comment
      | ID | Gene Review ID | Content    |
      | 1  | 1              | My comment |
    Then I see the gene review comment
      | Gene Review Comment ID |
      | 1                      |
    Examples:
      | username      |
      | TEST_Reviewer |
      | TEST_Curator  |

  Scenario Outline: Delete comment
    Given there are gene reviews
      | ID | Panel Gene ID | Rating                     | User       |
      | 1  | 1             | Green List (high evidence) | <username> |
    And there are gene review comments
      | ID | Gene Review ID | Content    | User       |
      | 1  | 1              | My comment | <username> |
    When I log in as "<username>"
    And I delete the gene review comment
      | Gene Review Comment ID |
      | 1                      |
    Then I do not see the gene review comment
      | Gene Review Comment ID |
      | 1                      |
    Examples:
      | username      |
      | TEST_Reviewer |
      | TEST_Curator  |

  @fail
  Scenario Outline: Cannot delete another user's review
    Given there are gene reviews
      | ID | Panel Gene ID | Rating                     | User      |
      | 1  | 1             | Green List (high evidence) | <creator> |
    When I log in as "<deleter>"
    Then I cannot delete the gene review
      | Gene Review ID |
      | 1              |
    Examples:
      | creator       | deleter       |
      | TEST_Curator  | TEST_Reviewer |
      | TEST_Reviewer | TEST_Curator  |

  @fail
  Scenario Outline: Cannot delete another user's comment
    And there are gene reviews
      | ID | Panel Gene ID | Rating                     | User      |
      | 1  | 1             | Green List (high evidence) | <creator> |
    And there are gene review comments
      | ID | Gene Review ID | Content    | User      |
      | 1  | 1              | My comment | <creator> |
    When I log in as "<deleter>"
    Then I cannot delete the gene review comment
      | Gene Review Comment ID |
      | 1                      |
    Examples:
      | creator       | deleter       |
      | TEST_Curator  | TEST_Reviewer |
      | TEST_Reviewer | TEST_Curator  |
