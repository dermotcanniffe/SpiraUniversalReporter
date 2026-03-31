Feature: CLI Operational Modes
  As a DevOps engineer
  I want a single command with clear modes
  So that I can validate setup and send results in my pipeline

  Scenario: Help mode displays usage and env vars
    When I run spira-report with --help
    Then the output should include "spira-report"
    And the output should include "SPIRA_URL"
    And the output should include "SPIRA_RESULTS_DIR"
    And the output should include "--preflight"
    And the exit code should be 0

  @integration
  Scenario: Preflight mode validates connectivity
    Given the environment is configured
    When I run spira-report with --preflight
    Then the output should include "Authentication OK"
    And the output should include "Release"
    And the output should include "Test set OK"
    And the exit code should be 0

  Scenario: Auto-sense finds Allure results in a directory
    Given a temporary directory containing a valid Allure JSON file
    When I run the auto-sense discovery on that directory
    Then the discovered format should be "allure-json"

  Scenario: Auto-sense finds JUnit results in a directory
    Given a temporary directory containing a valid JUnit XML file
    When I run the auto-sense discovery on that directory
    Then the discovered format should be "junit-xml"

  Scenario: Auto-sense finds ExtentReports in a directory
    Given a temporary directory containing a Summary.html
    When I run the auto-sense discovery on that directory
    Then the discovered format should be "extent-html"

  Scenario: Auto-sense returns None for empty directory
    Given an empty temporary directory
    When I run the auto-sense discovery on that directory
    Then no results should be discovered

  Scenario: Results path resolves from SPIRA_RESULTS_DIR env var
    Given SPIRA_RESULTS_DIR is set to "/some/path"
    When I resolve the results path with no CLI argument
    Then the resolved path should be "/some/path"

  Scenario: CLI argument overrides SPIRA_RESULTS_DIR
    Given SPIRA_RESULTS_DIR is set to "/env/path"
    When I resolve the results path with CLI argument "/cli/path"
    Then the resolved path should be "/cli/path"

  Scenario: Falls back to cwd when nothing is set
    Given SPIRA_RESULTS_DIR is not set
    When I resolve the results path with no CLI argument
    Then the resolved path should be "."
