Feature: Create Cucumber BDD tests for the tool
  As a developer
  I want comprehensive BDD tests for the integration script
  So that I can verify functionality before deployment

  Scenario: Create feature file for configuration loading
    Given I am writing Cucumber tests
    When I create a feature file for configuration loading
    Then it should include scenarios for CLI argument parsing
    And it should include scenarios for environment variable loading
    And it should include scenarios for priority rules

  Scenario: Create feature file for test result parsing
    Given I am writing Cucumber tests
    When I create a feature file for test result parsing
    Then it should include scenarios for JUnit XML parsing
    And it should include scenarios for Allure JSON parsing
    And it should include scenarios for format detection

  Scenario: Create feature file for Spira API communication
    Given I am writing Cucumber tests
    When I create a feature file for Spira API communication
    Then it should include scenarios for authentication
    And it should include scenarios for creating test runs
    And it should include scenarios for uploading evidence
    And it should use mock API responses

  Scenario: Create feature file for error handling
    Given I am writing Cucumber tests
    When I create a feature file for error handling
    Then it should include scenarios for invalid configuration
    And it should include scenarios for parsing errors
    And it should include scenarios for API errors

  Scenario: Implement step definitions for configuration scenarios
    Given I have configuration feature files
    When I implement step definitions
    Then I should have steps for setting CLI arguments
    And I should have steps for setting environment variables
    And I should have steps for verifying configuration values
