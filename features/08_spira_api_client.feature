Feature: Spira API Client core functionality
  As a DevOps engineer
  I want to authenticate with Spira and create test runs
  So that test results are sent to the test management system

  Scenario: Initialize Spira API Client with credentials
    Given I have Spira credentials:
      | field    | value                      |
      | base_url | https://spira.example.com  |
      | username | testuser                   |
      | api_key  | secret123                  |
    When I initialize the Spira API Client
    Then the client should be created successfully

  Scenario: Authenticate with valid credentials
    Given I have a Spira API Client
    When I authenticate with valid credentials
    Then the authentication should succeed
    And the authentication state should be cached

  Scenario: Validate Spira URL format
    Given I have Spira credentials with invalid URL "not-a-url"
    When I attempt to initialize the Spira API Client
    Then a ValidationError should be raised

  Scenario: Handle authentication failure
    Given I have a Spira API Client
    When I authenticate with invalid credentials
    Then an AuthenticationError should be raised
    And the error should include the HTTP status code
    And the error should include the response message

  Scenario: Create test run with valid data
    Given I have an authenticated Spira API Client
    And I have test run data:
      | field           | value                    |
      | test_case_id    | TC:123                   |
      | execution_status| PASSED                   |
      | start_time      | 2024-01-01T10:00:00Z     |
      | end_time        | 2024-01-01T10:01:00Z     |
    When I create a test run for project 1 and test set 10
    Then the test run should be created successfully
    And the response should contain a test run ID
    And the test run ID should be logged

  Scenario: Build correct POST request for test run
    Given I have an authenticated Spira API Client
    When I create a test run for project 123 and test set 456
    Then the request should be sent to the correct endpoint

  Scenario: Include all required fields in test run request
    Given I have an authenticated Spira API Client
    And I have test run data with all fields
    When I create a test run
    Then the request body should include required fields

  Scenario: Handle API error response
    Given I have an authenticated Spira API Client
    When the Spira API returns an error response with status 400
    Then an APIError should be raised
    And the error should include status code 400

  Scenario: Validate release exists
    Given I have an authenticated Spira API Client
    When I validate release 5 in project 1
    Then the release should be validated successfully
    And the release name should be logged

  Scenario: Handle release not found
    Given I have an authenticated Spira API Client
    When I validate a non-existent release
    Then an APIError should be raised
    And the error should indicate the release was not found
    And the error should indicate releases cannot be auto-created

  Scenario: Get existing test set
    Given I have an authenticated Spira API Client
    When I check for test set 10 in project 1
    Then the test set should be found
    And the test set ID should be returned

  Scenario: Auto-create test set when not found
    Given I have an authenticated Spira API Client
    And auto_create_test_sets is enabled
    When I check for a non-existent test set
    Then a new test set should be created
    And the new test set ID should be returned

  Scenario: Fail when test set not found and auto-create disabled
    Given I have an authenticated Spira API Client
    And auto_create_test_sets is disabled
    When I check for a non-existent test set
    Then an APIError should be raised

  Scenario: Search test case by custom property
    Given I have an authenticated Spira API Client
    When I search for test cases with Custom_04 = "test-hash"
    Then the search request should POST to the test-cases/search endpoint
    And the filter should include the custom property name and value

  Scenario: Create test case with custom property
    Given I have an authenticated Spira API Client
    When I create a test case with custom property Custom_04 = "test-hash"
    Then the test case should be created
    And the custom property should be included in the request payload
