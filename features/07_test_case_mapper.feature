Feature: Test Case Mapper
  As a test manager
  I want test results mapped to Spira test cases
  So that execution history is tracked correctly

  Scenario: Extract TC ID from test name with bracket format
    Given I have a test case mapper
    When I extract the test case ID from "User can login [TC:123]"
    Then I should receive test case ID 123

  Scenario: Extract TC ID from test name with prefix format
    Given I have a test case mapper
    When I extract the test case ID from "TC-456: Checkout test"
    Then I should receive test case ID 456

  Scenario: Extract TC ID from test name with parentheses format
    Given I have a test case mapper
    When I extract the test case ID from "Login test (TC:789)"
    Then I should receive test case ID 789

  Scenario: Extract TC ID from test name with compact format
    Given I have a test case mapper
    When I extract the test case ID from "TC101 validation"
    Then I should receive test case ID 101

  Scenario: Return None when no TC ID found
    Given I have a test case mapper
    When I extract the test case ID from "Login test with no ID"
    Then I should receive None

  Scenario: Extract TC ID from Allure raw data labels
    Given I have a test case mapper
    And I have Allure raw data with a testCaseId label value of "42"
    When I extract the test case ID from the raw data
    Then I should receive test case ID 42

  Scenario: Extract TC ID from full name
    Given I have a test case mapper
    And I have raw data with fullName "suite/TC-200: Login test"
    When I extract the test case ID from the raw data
    Then I should receive test case ID 200

  Scenario: Extract automation ID from Allure testCaseId hash
    Given I have a test case mapper
    And I have Allure raw data with testCaseId "e82fecfb3ac31d524a5d9c18c7cec49e"
    When I extract the automation ID
    Then I should receive "e82fecfb3ac31d524a5d9c18c7cec49e"

  Scenario: Extract automation ID from JUnit classname.name
    Given I have a test case mapper
    And I have JUnit raw data with classname "com.example.LoginTest" and name "testLogin"
    When I extract the automation ID
    Then I should receive "com.example.LoginTest.testLogin"

  Scenario: Extract automation ID from ExtentReports test name
    Given I have a test case mapper
    And I have ExtentReports raw data with name "Web_TC01"
    When I extract the automation ID
    Then I should receive None
    # ExtentReports raw_data has no testCaseId or classname, falls through

  Scenario: Return None for automation ID when no identifier available
    Given I have a test case mapper
    And I have empty raw data
    When I extract the automation ID
    Then I should receive None
