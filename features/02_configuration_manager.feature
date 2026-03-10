Feature: Configuration Manager
  As a DevOps engineer
  I want to configure the integration script via CLI or environment variables
  So that I can adapt it to different CI/CD environments

  Scenario: Load configuration from CLI arguments
    Given I have a configuration manager
    When I provide the following CLI arguments:
      | argument      | value                           |
      | --spira-url   | https://spira.example.com       |
      | --project-id  | 123                             |
      | --test-set-id | 456                             |
      | --username    | testuser                        |
      | --api-key     | secret123                       |
      | --results-file| /path/to/results.xml            |
      | --result-type | junit-xml                       |
    Then the configuration should be loaded successfully
    And the spira_url should be "https://spira.example.com"
    And the project_id should be "123"

  Scenario: Load configuration from environment variables
    Given I have a configuration manager
    When I set the following environment variables:
      | variable              | value                           |
      | SPIRA_URL             | https://spira.example.com       |
      | SPIRA_PROJECT_ID      | 123                             |
      | SPIRA_TEST_SET_ID     | 456                             |
      | SPIRA_USERNAME        | testuser                        |
      | SPIRA_API_KEY         | secret123                       |
      | SPIRA_RESULTS_FILE    | /path/to/results.xml            |
      | SPIRA_RESULT_TYPE     | junit-xml                       |
    Then the configuration should be loaded successfully
    And the spira_url should be "https://spira.example.com"

  Scenario: CLI arguments override environment variables
    Given I have a configuration manager
    And I set the environment variable "SPIRA_URL" to "https://env.example.com"
    When I provide the CLI argument "--spira-url" with value "https://cli.example.com"
    Then the spira_url should be "https://cli.example.com"

  Scenario: Validate required parameters are present
    Given I have a configuration manager
    When I attempt to load configuration without providing "spira-url"
    Then a ConfigurationError should be raised
    And the error message should indicate "spira-url is required"

  Scenario: Validate Spira URL format
    Given I have a configuration manager
    When I provide an invalid URL "not-a-valid-url"
    Then a ConfigurationError should be raised
    And the error message should indicate "Invalid URL format"

  Scenario: Validate file paths exist
    Given I have a configuration manager
    When I provide a results file path that does not exist
    Then a ConfigurationError should be raised
    And the error message should indicate "Results file not found"

  Scenario: Mask API key values in logs
    Given I have a configuration manager with API key "secret123456"
    When I log the configuration
    Then the API key should be masked as "secr********"
    And the full API key should not appear in logs
