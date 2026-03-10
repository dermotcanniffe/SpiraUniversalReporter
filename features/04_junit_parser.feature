Feature: JUnit XML Parser
  As a test automation engineer using TestNG
  I want to parse JUnit XML results
  So that my test outcomes are sent to Spira

  Scenario: Parse valid JUnit XML file with single testsuite
    Given I have a JUnit parser
    And I have a valid JUnit XML file with single testsuite:
      """
      <?xml version="1.0" encoding="UTF-8"?>
      <testsuite name="TestSuite" tests="2" failures="1" time="1.234">
        <testcase name="test_login" classname="LoginTests" time="0.5"/>
        <testcase name="test_logout" classname="LoginTests" time="0.734">
          <failure message="Assertion failed">Expected true but got false</failure>
        </testcase>
      </testsuite>
      """
    When I parse the file
    Then I should get 2 test results
    And test result 0 should have name "test_login"
    And test result 0 should have status "PASSED"
    And test result 1 should have name "test_logout"
    And test result 1 should have status "FAILED"
    And test result 1 should have error message "Expected true but got false"

  Scenario: Parse JUnit XML with multiple testsuites
    Given I have a JUnit parser
    And I have a JUnit XML file with multiple testsuites
    When I parse the file
    Then I should get test results from all testsuites

  Scenario: Extract test duration from time attribute
    Given I have a JUnit parser
    And I have a JUnit XML testcase with time="1.234"
    When I parse the file
    Then the test result should have duration 1.234 seconds

  Scenario: Map skipped tests to SKIP status
    Given I have a JUnit parser
    And I have a JUnit XML testcase with <skipped/> element
    When I parse the file
    Then the test result should have status "SKIPPED"

  Scenario: Extract error messages from error elements
    Given I have a JUnit parser
    And I have a JUnit XML testcase with <error> element
    When I parse the file
    Then the test result should have the error message from the element

  Scenario: Extract evidence file paths from system-out
    Given I have a JUnit parser
    And I have a JUnit XML with system-out containing "EVIDENCE: /path/to/screenshot.png"
    When I parse the file
    Then the test result should have evidence file "/path/to/screenshot.png"

  Scenario: Handle invalid XML gracefully
    Given I have a JUnit parser
    And I have an invalid XML file
    When I attempt to parse the file
    Then a ParseError should be raised
    And the error message should indicate "Invalid XML format"

  Scenario: Support TestNG-compatible XML format
    Given I have a JUnit parser
    And I have a TestNG-generated JUnit XML file
    When I parse the file
    Then the test results should be extracted correctly
