Feature: Stateless Test Case Matching via Custom Properties
  As a test manager
  I want test results automatically matched to Spira test cases via custom properties
  So that no local mapping files or test name modifications are needed

  Scenario: Search for test case by custom property value
    Given I have an authenticated Spira API Client
    And a test case exists with Custom_04 set to "e82fecfb3ac31d524a5d9c18c7cec49e"
    When I search for a test case with Custom_04 = "e82fecfb3ac31d524a5d9c18c7cec49e"
    Then I should receive the matching test case ID

  Scenario: Return None when no test case matches custom property
    Given I have an authenticated Spira API Client
    And no test case has Custom_04 set to "nonexistent-hash"
    When I search for a test case with Custom_04 = "nonexistent-hash"
    Then I should receive None

  Scenario: Create test case with custom property value
    Given I have an authenticated Spira API Client
    When I create a test case "Login Test" with Custom_04 = "abc123hash"
    Then the test case should be created successfully
    And the custom property Custom_04 should be set to "abc123hash"

  Scenario: Full matching flow - existing test case found
    Given I have an authenticated Spira API Client
    And automation_id_field is configured as "Custom_04"
    And a test result has automation ID "e82fecfb3ac31d524a5d9c18c7cec49e"
    And a test case exists with that automation ID in Custom_04
    When the matching flow runs
    Then the existing test case ID should be used for the test run

  Scenario: Full matching flow - auto-create new test case
    Given I have an authenticated Spira API Client
    And automation_id_field is configured as "Custom_04"
    And auto_create_test_cases is enabled
    And a test result has automation ID "new-hash-never-seen"
    And no test case exists with that automation ID
    When the matching flow runs
    Then a new test case should be created with Custom_04 = "new-hash-never-seen"
    And the new test case ID should be used for the test run

  Scenario: Full matching flow - skip when auto-create disabled
    Given I have an authenticated Spira API Client
    And automation_id_field is configured as "Custom_04"
    And auto_create_test_cases is disabled
    And a test result has automation ID "unknown-hash"
    And no test case exists with that automation ID
    When the matching flow runs
    Then the test result should be skipped
    And a warning should be logged

  Scenario: Fallback to TC ID regex when automation_id_field not configured
    Given automation_id_field is not configured
    And a test result has name "Login test [TC:707]"
    When the matching flow runs
    Then TC ID 707 should be extracted from the test name
