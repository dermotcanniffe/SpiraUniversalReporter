Feature: CLI entry point
  As a DevOps engineer
  I want a command-line interface for the integration script
  So that I can run it in CI/CD pipelines

  Scenario: Define all CLI arguments
    Given I have a CLI entry point
    When I request help information
    Then the following arguments should be defined:
      | argument         | description                          |
      | --spira-url      | Spira instance URL                   |
      | --project-id     | Spira project identifier             |
      | --test-set-id    | Spira test set identifier            |
      | --username       | Spira username                       |
      | --api-key        | Spira API key                        |
      | --results-file   | Path to test results file            |
      | --result-type    | Test result format type              |
      | --mapping-file   | Path to test case mapping file       |

  Scenario: Display help text for each argument
    Given I have a CLI entry point
    When I run the script with "--help"
    Then help text should be displayed for all arguments
    And usage examples should be shown

  Scenario: Wire CLI to main orchestrator
    Given I have a CLI entry point
    When I run the script with valid arguments
    Then the arguments should be passed to the main orchestrator
    And the orchestrator should execute

  Scenario: Configure logging to stdout for progress
    Given I have a CLI entry point
    When I run the script
    Then progress messages should be logged to stdout
    And the log level should be INFO

  Scenario: Configure logging to stderr for errors
    Given I have a CLI entry point
    When an error occurs during execution
    Then error messages should be logged to stderr
    And the log level should be ERROR
