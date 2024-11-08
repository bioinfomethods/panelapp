Feature: Navigation
  Scenario: Panels
    When I am on the home page
    Then I can navigate to the panels page

  Scenario: Genes and entities
    When I am on the home page
    Then I can navigate to the genes and entities page

  Scenario: Activities
    When I am on the home page
    Then I can navigate to the activities page

  Scenario: Login
    When I am on the home page
    Then I can navigate to the login page

  Scenario: Account registration
    When I am on the home page
    Then I can navigate to the account registration page

  Scenario: Home page
    When I am on the panels page
    Then I can navigate to the home page

  Scenario: Add panel
    Given I log in as "TEST_Curator"
    When I am on the home page
    Then I can navigate to the add panel page

  Scenario: Import panel
    Given I log in as "TEST_Curator"
    When I am on the home page
    Then I can navigate to the import panel page

  Scenario: Cannot navigate to Add panel page
    When I am on the home page
    Then I cannot navigate to the add panel page

  Scenario: Cannot navigate to Import panel page
    When I am on the home page
    Then I cannot navigate to the import panel page
