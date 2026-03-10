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

  Scenario: Detect result type from XML file extension
    Given I have a parser factory
    And I have a file named "results.xml"
    When I detect the result type
    Then it detects "junit-xml"

  Scenario: Detect result type from JSON file extension
    Given I have a parser factory
    And I have a file named "allure-results.json"
    When I detect the result type
    Then it detects "allure-json"

  Scenario: Detect result type from XML file content
    Given I have a parser factory
    And I have a file with XML content starting with "<testsuite"
    When I detect the result type from content
    Then it detects "junit-xml"

  Scenario: Detect result type from Allure JSON content
    Given I have a parser factory
    And I have a file with JSON content containing "uuid" and "status" fields
    When I detect the result type from content
    Then it detects "allure-json"

  Scenario: Raise error for unsupported format
    Given I have a parser factory
    When I request a parser for type "unsupported-format"
    Then an UnsupportedFormatError should be raised
    And the error message should list supported formats:
      | format       |
      | junit-xml    |
      | allure-json  |

  Scenario: List supported parser types
    Given I have a parser factory
    When I request the list of supported types
    Then I should receive:
      | type         |
      | junit-xml    |
      | allure-json  |
