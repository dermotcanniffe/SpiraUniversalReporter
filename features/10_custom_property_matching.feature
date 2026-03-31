Feature: Stateless Test Case Matching via Custom Properties
  As a test manager
  I want test results automatically matched to Spira test cases via custom properties
  So that no local mapping files or test name modifications are needed

  Scenario: Extract automation ID from Allure testCaseId hash
    Given I have a test case mapper
    And I have raw data with testCaseId "e82fecfb3ac31d524a5d9c18c7cec49e"
    When I extract the automation ID
    Then the automation ID should be "e82fecfb3ac31d524a5d9c18c7cec49e"

  Scenario: Extract automation ID from JUnit classname.name
    Given I have a test case mapper
    And I have raw data with classname "com.example.LoginTest" and name "testLogin"
    When I extract the automation ID
    Then the automation ID should be "com.example.LoginTest.testLogin"

  Scenario: Return None when no automation ID available
    Given I have a test case mapper
    And I have raw data with no identifiers
    When I extract the automation ID
    Then the automation ID should be None

  Scenario: Fallback to TC ID regex when no automation_id_field
    Given I have a test case mapper
    When I extract TC ID from "Login test [TC:707]"
    Then the TC ID should be 707

  Scenario: Fallback returns None for test names without TC IDs
    Given I have a test case mapper
    When I extract TC ID from "Login test with no ID"
    Then the TC ID should be None

  @integration
  Scenario: Search Spira for test case by custom property
    Given the environment is configured
    And SPIRA_AUTOMATION_ID_FIELD is defined
    And I have an authenticated client from environment
    When I search for a test case with a known automation ID
    Then the search should return a result or empty list without error

  @integration
  Scenario: Create test case with custom property and find it
    Given the environment is configured
    And SPIRA_AUTOMATION_ID_FIELD is defined
    And I have an authenticated client from environment
    When I create a test case with a unique automation ID
    And I search for that automation ID
    Then the search should return the created test case
