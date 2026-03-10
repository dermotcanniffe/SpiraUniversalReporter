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
