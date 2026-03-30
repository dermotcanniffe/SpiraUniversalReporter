Feature: Evidence Upload Handler
  As a test analyst
  I want screenshots and logs attached to test runs
  So that I can investigate failures

  Scenario: Upload evidence file successfully
    Given I have an authenticated Spira API Client
    And I have a test run with ID "TR:789"
    And I have an evidence file "/path/to/screenshot.png"
    When I upload the evidence file
    Then the file should be uploaded successfully
    And the request should be sent to "/test-runs/TR:789/attachments"
    And the Content-Type header should be "multipart/form-data"

  Scenario: Read file in binary mode
    Given I have an authenticated Spira API Client
    And I have an evidence file "/path/to/video.mp4"
    When I upload the evidence file
    Then the file should be read in binary mode

  Scenario: Preserve original filename
    Given I have an authenticated Spira API Client
    And I have an evidence file "/path/to/screenshot.png"
    When I upload the evidence file
    Then the attachment should have filename "screenshot.png"

  Scenario: Support multiple MIME types
    Given I have an authenticated Spira API Client
    When I upload evidence files with the following types:
      | file_extension | mime_type   |
      | .png           | image/png   |
      | .jpeg          | image/jpeg  |
      | .mp4           | video/mp4   |
      | .txt           | text/plain  |
    Then all files should be uploaded with correct MIME types

  Scenario: Log warning if file doesn't exist
    Given I have an authenticated Spira API Client
    And I have an evidence file path "/path/to/missing.png" that doesn't exist
    When I attempt to upload the evidence file
    Then a warning should be logged indicating "Evidence file not found: /path/to/missing.png"
    And the execution should continue without failing

  Scenario: Log error if upload fails
    Given I have an authenticated Spira API Client
    And I have an evidence file "/path/to/screenshot.png"
    When the upload fails with HTTP 500
    Then an error should be logged indicating "Failed to upload evidence"
    And the execution should continue with other files

  Scenario: Track upload success and failure counts
    Given I have an authenticated Spira API Client
    When I upload 5 evidence files with 3 successes and 2 failures
    Then the success count should be 3
    And the failure count should be 2

  Scenario: Continue processing after upload failure
    Given I have an authenticated Spira API Client
    And I have 3 evidence files to upload
    When the second file upload fails
    Then the first file should be uploaded
    And the third file should still be uploaded
    And the execution should not be interrupted
