@integration
Feature: Pre-flight Validation
  As a DevOps engineer deploying the Spira integration tool
  I want to validate my configuration and connectivity before running
  So that I can catch setup issues before they cause pipeline failures

  Scenario: All required environment variables are defined
    Given the environment is configured
    Then SPIRA_URL should be defined and non-empty
    And SPIRA_USERNAME should be defined and non-empty
    And SPIRA_API_KEY should be defined and non-empty
    And SPIRA_PROJECT_ID should be defined and non-empty
    And SPIRA_TEST_SET_ID should be defined and non-empty
    And SPIRA_RELEASE_ID should be defined and non-empty

  Scenario: Spira URL is reachable
    Given the environment is configured
    When I check connectivity to the Spira URL
    Then the Spira instance should respond

  Scenario: Spira credentials are valid
    Given the environment is configured
    When I authenticate with the configured credentials
    Then authentication should succeed
    And the authenticated user should have access to the configured project

  Scenario: Configured release exists in the project
    Given the environment is configured
    And I am authenticated with Spira
    When I validate the configured release
    Then the release should exist
    And the release name should be returned

  Scenario: Configured test set exists or can be created
    Given the environment is configured
    And I am authenticated with Spira
    When I check the configured test set
    Then the test set should exist or be creatable

  Scenario: Sample test result files can be parsed
    Given the environment is configured
    And sample Allure results exist at "examples/sample-allure-results.json"
    When I parse the sample Allure results
    Then at least 1 test result should be extracted
    And each result should have a name and status

  Scenario: Sample JUnit results can be parsed
    Given the environment is configured
    And sample JUnit results exist at "examples/sample-junit-results.xml"
    When I parse the sample JUnit results
    Then at least 1 test result should be extracted
    And each result should have a name and status

  Scenario: Client ExtentReports results can be parsed
    Given the environment is configured
    And client ExtentReports results exist at "examples/client-testng-results"
    When I parse the client ExtentReports results
    Then at least 1 test result should be extracted
    And each result should have a name and status
    And each result should have evidence files discovered

  Scenario: A test run can be created and retrieved
    Given the environment is configured
    And I am authenticated with Spira
    And the configured release is valid
    And the configured test set is ready
    When I create a test run with a sample passed result
    Then the test run should be created in Spira
    And the test run ID should be a positive integer
