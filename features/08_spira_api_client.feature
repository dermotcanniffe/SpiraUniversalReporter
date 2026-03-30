@integration
Feature: Spira API Client
  As a DevOps engineer
  I want to verify the Spira API client works correctly
  So that test results can be sent reliably

  Scenario: Authenticate with configured credentials
    Given the environment is configured
    When I create a Spira API client from environment
    And I authenticate
    Then authentication should succeed

  Scenario: Reject invalid credentials
    Given the environment is configured
    When I create a Spira API client with wrong API key
    And I attempt to authenticate
    Then an AuthenticationError should be raised

  Scenario: Validate URL format rejects garbage
    When I create a Spira API client with URL "not-a-url"
    Then a ValidationError should be raised

  Scenario: Validate configured release exists
    Given the environment is configured
    And I have an authenticated client from environment
    When I validate the configured release
    Then the release should exist
    And the release data should include a name

  Scenario: Reject non-existent release
    Given the environment is configured
    And I have an authenticated client from environment
    When I validate release ID 999999
    Then an APIError should be raised with "not found"

  Scenario: Get existing test set
    Given the environment is configured
    And I have an authenticated client from environment
    When I check the configured test set
    Then the test set should be found

  Scenario: Create test run with sample data
    Given the environment is configured
    And I have an authenticated client from environment
    When I create a test run with sample data
    Then the test run ID should be returned
    And the test run ID should be a positive integer
