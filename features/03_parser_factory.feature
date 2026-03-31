Feature: Parser Factory and result type detection
  As a test automation engineer
  I want the script to identify and load the correct parser
  So that my test results are correctly interpreted

  Scenario: Get parser by explicit type - JUnit
    Given I have a parser factory
    When I request a parser for type "junit-xml"
    Then I should receive a JUnitParser instance

  Scenario: Get parser by explicit type - Allure
    Given I have a parser factory
    When I request a parser for type "allure-json"
    Then I should receive an AllureParser instance

  Scenario: Get parser by explicit type - ExtentReports
    Given I have a parser factory
    When I request a parser for type "extent-html"
    Then I should receive an ExtentParser instance

  Scenario: Auto-detect JUnit XML from file
    Given I have a parser factory
    And I have a valid JUnit XML file
    When I detect the result type
    Then it detects "junit-xml"

  Scenario: Auto-detect Allure JSON from file
    Given I have a parser factory
    And I have a valid Allure JSON file
    When I detect the result type
    Then it detects "allure-json"

  Scenario: Auto-detect ExtentReports from directory
    Given I have a parser factory
    And I have a directory containing Summary.html
    When I detect the result type
    Then it detects "extent-html"

  Scenario: Raise error for unsupported format
    Given I have a parser factory
    When I request a parser for type "unsupported-format"
    Then an UnsupportedFormatError should be raised
    And the error message should list supported formats

  Scenario: List supported parser types
    Given I have a parser factory
    When I request the list of supported types
    Then I should receive:
      | type         |
      | junit-xml    |
      | allure-json  |
      | extent-html  |

  Scenario: Register a custom parser at runtime
    Given I have a parser factory
    And I have a custom parser class with format_name "custom-csv"
    When I register the custom parser
    Then "custom-csv" should appear in the supported types list
    And I should be able to get a parser for "custom-csv"

  Scenario: Each parser declares can_parse for auto-detection
    Given I have a parser factory
    Then each registered parser should have a can_parse method
    And each registered parser should have a non-empty format_name
