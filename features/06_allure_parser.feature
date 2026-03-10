Feature: Allure JSON Parser
  As a test automation engineer using Cypress with Allure
  I want to parse Allure JSON results
  So that my test outcomes are sent to Spira

  Scenario: Parse valid Allure JSON file
    Given I have an Allure parser
    And I have a valid Allure JSON file:
      """
      {
        "uuid": "test-uuid-1",
        "name": "Login test",
        "status": "passed",
        "start": 1234567890000,
        "stop": 1234567891000,
        "attachments": []
      }
      """
    When I parse the file
    Then I should get 1 test result
    And the test result should have name "Login test"
    And the test result should have status "PASSED"

  Scenario: Map Allure status to TestStatus enum
    Given I have an Allure parser
    When I parse Allure results with the following statuses:
      | allure_status | expected_status |
      | passed        | PASSED          |
      | failed        | FAILED          |
      | broken        | FAILED          |
      | skipped       | SKIPPED         |
    Then the statuses should be mapped correctly

  Scenario: Extract timestamps from start and stop fields
    Given I have an Allure parser
    And I have an Allure result with start=1234567890000 and stop=1234567891000
    When I parse the file
    Then the test result should have start timestamp 1234567890000
    And the test result should have duration 1000 milliseconds

  Scenario: Extract error messages from statusDetails
    Given I have an Allure parser
    And I have an Allure result with statusDetails:
      """
      {
        "message": "Assertion failed: expected true but got false",
        "trace": "at LoginTest.test_login (login.spec.js:15:5)"
      }
      """
    When I parse the file
    Then the test result should have error message "Assertion failed: expected true but got false"
    And the test result should have stack trace containing "login.spec.js:15:5"

  Scenario: Extract evidence files from attachments
    Given I have an Allure parser
    And I have an Allure result with attachments:
      """
      [
        {"name": "Screenshot", "source": "screenshots/test-1.png", "type": "image/png"},
        {"name": "Video", "source": "videos/test-1.mp4", "type": "video/mp4"}
      ]
      """
    When I parse the file
    Then the test result should have 2 evidence files
    And evidence file 0 should be "screenshots/test-1.png"
    And evidence file 1 should be "videos/test-1.mp4"

  Scenario: Resolve relative paths for evidence files
    Given I have an Allure parser
    And the results directory is "/path/to/allure-results"
    And I have an attachment with source "screenshots/test.png"
    When I parse the file
    Then the evidence file path should be "/path/to/allure-results/screenshots/test.png"

  Scenario: Support PNG, JPEG, MP4 file types
    Given I have an Allure parser
    When I parse attachments with the following types:
      | type       | should_include |
      | image/png  | yes            |
      | image/jpeg | yes            |
      | video/mp4  | yes            |
      | text/plain | yes            |
    Then only supported file types should be included

  Scenario: Handle invalid JSON gracefully
    Given I have an Allure parser
    And I have an invalid JSON file
    When I attempt to parse the file
    Then a ParseError should be raised
    And the error message should indicate "Invalid JSON format"
