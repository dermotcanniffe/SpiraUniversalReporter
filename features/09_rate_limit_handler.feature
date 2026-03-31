Feature: Rate Limit Handler
  As a DevOps engineer
  I want the script to handle API rate limits gracefully
  So that pipeline execution is reliable

  Scenario: Client raises RateLimitError on HTTP 429
    Given I have a Spira API client
    When the API returns HTTP 429 for a test run creation
    Then a RateLimitError should be raised
    And the error message should contain "Rate limit"

  Scenario: Client handles non-429 errors as APIError
    Given I have a Spira API client
    When the API returns HTTP 500 for a test run creation
    Then an APIError should be raised
    And the error message should contain "500"
