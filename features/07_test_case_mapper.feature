Feature: Test Case Mapper
  As a test manager
  I want test results mapped to Spira test cases
  So that execution history is tracked correctly

  Scenario: Load mappings from JSON file
    Given I have a test case mapper
    And I have a mapping file "mappings.json":
      """
      {
        "test_login": "TC:123",
        "test_logout": "TC:124",
        "test_.*_password": "TC:125"
      }
      """
    When I load the mappings
    Then the mappings should be loaded successfully

  Scenario: Get test case ID by exact name match
    Given I have a test case mapper with mappings:
      | test_name   | test_case_id |
      | test_login  | TC:123       |
      | test_logout | TC:124       |
    When I get the test case ID for "test_login"
    Then I should receive "TC:123"

  Scenario: Get test case ID by regex pattern match
    Given I have a test case mapper with mappings:
      | pattern              | test_case_id |
      | test_.*_password     | TC:125       |
    When I get the test case ID for "test_reset_password"
    Then I should receive "TC:125"

  Scenario: Exact match takes priority over regex match
    Given I have a test case mapper with mappings:
      | mapping              | test_case_id |
      | test_login           | TC:123       |
      | test_.*              | TC:999       |
    When I get the test case ID for "test_login"
    Then I should receive "TC:123"

  Scenario: Log warning when no mapping found
    Given I have a test case mapper with no mappings
    When I get the test case ID for "unmapped_test"
    Then I should receive None
    And a warning should be logged indicating "No mapping found for unmapped_test"

  Scenario: Support multiple regex patterns
    Given I have a test case mapper with regex patterns:
      | pattern              | test_case_id |
      | test_.*_login        | TC:100       |
      | test_.*_logout       | TC:101       |
      | test_.*_password     | TC:102       |
    When I get test case IDs for the following tests:
      | test_name              | expected_id |
      | test_user_login        | TC:100      |
      | test_admin_logout      | TC:101      |
      | test_reset_password    | TC:102      |
    Then all mappings should be resolved correctly
