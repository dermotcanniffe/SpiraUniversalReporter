Feature: Main Orchestrator
  As a DevOps engineer
  I want the script to orchestrate the entire workflow
  So that test results are processed and sent to Spira

  Scenario: Execute complete workflow successfully
    Given I have valid configuration
    And I have a test results file
    And I have a mapping file
    When I run the main orchestrator
    Then the configuration should be loaded
    And the parser should be initialized
    And the test results should be parsed
    And the test case mapper should be initialized
    And the Spira API client should be initialized
    And test runs should be created for all results
    And evidence files should be uploaded
    And an execution summary should be generated

  Scenario: Initialize components in correct order
    Given I have valid configuration
    When I run the main orchestrator
    Then the components should be initialized in this order:
      | order | component            |
      | 1     | ConfigurationManager |
      | 2     | ParserFactory        |
      | 3     | TestCaseMapper       |
      | 4     | SpiraAPIClient       |

  Scenario: Parse test results file
    Given I have a JUnit XML results file with 5 tests
    When I run the main orchestrator
    Then 5 test results should be parsed

  Scenario: Create test runs for all mapped results
    Given I have 5 test results
    And 4 tests have mappings
    And 1 test has no mapping
    When I run the main orchestrator
    Then 4 test runs should be created in Spira
    And 1 test should be skipped with a warning

  Scenario: Upload evidence files for each test run
    Given I have 3 test results with evidence files
    When I run the main orchestrator
    Then evidence files should be uploaded for all 3 test runs

  Scenario: Generate execution summary
    Given I have completed test result processing
    When I generate the execution summary
    Then the summary should include total tests processed
    And the summary should include successful uploads
    And the summary should include failed uploads
    And the summary should include skipped tests
    And the summary should include evidence upload counts
    And the summary should include execution duration

  Scenario: Log execution summary to stdout
    Given I have an execution summary
    When I log the summary
    Then the summary should be written to stdout
    And the summary should be formatted as:
      """
      Execution Summary:
      - Total tests processed: 10
      - Successfully sent to Spira: 8
      - Failed to send: 1
      - Skipped (no mapping): 1
      - Evidence files uploaded: 15
      - Execution duration: 12.5 seconds
      """

  Scenario: Handle exceptions in main execution
    Given I have valid configuration
    When an exception occurs during execution
    Then the exception should be caught
    And the error should be logged to stderr
    And the script should exit with non-zero status code

  Scenario: Return exit code 0 on success
    Given I have valid configuration
    When the execution completes successfully
    Then the script should exit with status code 0

  Scenario: Return non-zero exit code on failure
    Given I have valid configuration
    When the execution fails
    Then the script should exit with a non-zero status code

  Scenario: Ensure partial failures don't prevent summary
    Given I have 10 test results
    When 2 test runs fail to create
    Then the execution should continue
    And the remaining 8 test runs should be created
    And the execution summary should still be generated
    And the summary should reflect the 2 failures
