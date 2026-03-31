Feature: Rate Limit Handler
  As a DevOps engineer
  I want the script to handle API rate limits gracefully
  So that pipeline execution is reliable

  Scenario: Retry with exponential backoff on HTTP 429
    Given I have a Spira API client
    When the API returns HTTP 429 then 200
    Then the request should succeed after retry
    And the retry should have waited before retrying

  Scenario: Raise RateLimitError after max retries exhausted
    Given I have a Spira API client
    When the API returns HTTP 429 for all retries
    Then a RateLimitError should be raised
    And the error message should contain "Rate limit exceeded"

  Scenario: Non-429 errors are raised as APIError immediately
    Given I have a Spira API client
    When the API returns HTTP 500 for a test run creation
    Then an APIError should be raised
    And the error message should contain "500"
