Feature: Rate Limit Handler
  As a DevOps engineer
  I want the script to handle API rate limits gracefully
  So that pipeline execution is reliable

  Scenario: Detect HTTP 429 rate limit response
    Given I have a Spira API Client
    When the Spira API returns HTTP 429
    Then the client should detect it as a rate limit response

  Scenario: Retry with exponential backoff
    Given I have a Spira API Client
    When the Spira API returns HTTP 429
    Then the client should wait 1 second before retry 1
    And the client should wait 2 seconds before retry 2
    And the client should wait 4 seconds before retry 3

  Scenario: Log retry attempts
    Given I have a Spira API Client
    When the Spira API returns HTTP 429
    And the client retries the request
    Then a log message should indicate "Retry attempt 1 of 3"

  Scenario: Succeed after retry
    Given I have a Spira API Client
    When the Spira API returns HTTP 429 on first attempt
    And the Spira API returns HTTP 200 on second attempt
    Then the request should succeed
    And the response should be returned

  Scenario: Raise error after max retries exhausted
    Given I have a Spira API Client
    When the Spira API returns HTTP 429 for all 3 retry attempts
    Then a RateLimitError should be raised
    And the error message should indicate "Rate limit exceeded after 3 retries"

  Scenario: Apply rate limiting to all API requests
    Given I have a Spira API Client
    When I make the following API requests:
      | request_type     |
      | create_test_run  |
      | upload_evidence  |
    Then rate limiting should be applied to all requests
