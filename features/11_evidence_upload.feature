Feature: Evidence Upload Handler
  As a test analyst
  I want screenshots and logs attached to test runs
  So that I can investigate failures

  Scenario: Skip upload gracefully when file does not exist
    Given I have an authenticated Spira API client
    When I attempt to upload a non-existent file "/tmp/does_not_exist.png"
    Then the upload should be skipped without raising an error

  Scenario: Read evidence file in binary mode
    Given I have a temporary PNG evidence file
    When I read the evidence file
    Then the file content should be bytes not string

  Scenario: Preserve original filename in upload payload
    Given I have a temporary evidence file named "screenshot_login.png"
    When I prepare the upload payload
    Then the payload filename should be "screenshot_login.png"

  @integration
  Scenario: Upload real evidence file to Spira
    Given the environment is configured
    And I have an authenticated client from environment
    And I have a temporary PNG evidence file
    When I create a test run and upload the evidence file
    Then the evidence should be uploaded successfully
