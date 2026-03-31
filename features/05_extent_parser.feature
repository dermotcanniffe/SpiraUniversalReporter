Feature: ExtentReports HTML Parser
  As a test automation engineer using Selenium with ExtentReports
  I want to parse ExtentReports HTML results
  So that my test outcomes are sent to Spira without modifying my framework

  Scenario: Parse valid ExtentReports directory
    Given I have an ExtentReports parser
    And I have a directory containing Summary.html with 2 test cases
    When I parse the directory
    Then I should get 2 test results

  Scenario: Extract test case names from HTML nodes
    Given I have an ExtentReports parser
    And I have a Summary.html with test "Web_TC01"
    When I parse the file
    Then the test result should have name "Web_TC01"

  Scenario: Map ExtentReports status to TestStatus enum
    Given I have an ExtentReports parser
    When I parse results with the following statuses:
      | extent_status | expected_status |
      | pass          | PASSED          |
      | fail          | FAILED          |
      | fatal         | FAILED          |
      | error         | FAILED          |
      | warning       | CAUTION         |
      | skip          | SKIPPED         |
    Then the statuses should be mapped correctly

  Scenario: Extract timestamps and durations
    Given I have an ExtentReports parser
    And I have a test node with time "Mar 26, 2026 06:55:58 PM" and duration "0h 0m 56s+560ms"
    When I parse the file
    Then the test result should have a valid start timestamp
    And the test result should have duration approximately 56.56 seconds

  Scenario: Extract error messages from step details
    Given I have an ExtentReports parser
    And I have a test node with failed steps containing error details
    When I parse the file
    Then the test result should have an error message

  Scenario: Discover screenshots from per-test directories
    Given I have an ExtentReports parser
    And I have a test "Web_TC01" with a Screenshots directory containing 4 PNG files
    When I parse the directory
    Then the test result should have 4 evidence files
    And each evidence file should be a PNG path

  Scenario: Discover consolidated screenshot documents
    Given I have an ExtentReports parser
    And I have a test "Web_TC01" with a ConsolidatedScreenshots directory containing a DOCX file
    When I parse the directory
    Then the evidence files should include the DOCX file

  Scenario: Find Summary.html up to 2 levels deep
    Given I have an ExtentReports parser
    And Summary.html is nested 2 directories deep
    When I parse the top-level directory
    Then the parser should find and parse Summary.html

  Scenario: Raise error when Summary.html not found
    Given I have an ExtentReports parser
    And I have an empty directory
    When I attempt to parse the directory
    Then a ParseError should be raised
    And the error message should indicate Summary.html was not found
