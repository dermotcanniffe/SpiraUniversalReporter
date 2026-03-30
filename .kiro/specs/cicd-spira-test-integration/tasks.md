# Implementation Plan: CI/CD Spira Test Integration

## Overview

This plan implements a Python-based CLI tool that parses test results from CI/CD pipelines (JUnit XML from TestNG, Allure JSON from Cypress) and transmits them to Spira test management system via REST API. The implementation follows a pluggable parser architecture with robust error handling, secure credential management, and comprehensive logging.

## Tasks

- [x] 1. Set up project structure and core interfaces
  - Create Python package structure with appropriate directories
  - Define core data models (TestResult, TestStatus, Configuration, TestCaseMapping, SpiraTestRun, ExecutionSummary)
  - Define TestResultParser abstract base class interface
  - Set up logging configuration
  - Create requirements.txt with dependencies (requests, pytest, cucumber)
  - _Requirements: 1.1, 1.4, 2.1-2.8, 3.1-3.4_

- [x] 2. Implement Configuration Manager
  - [x] 2.1 Create configuration loading from CLI arguments and environment variables
    - Implement argument parser using argparse
    - Implement environment variable reader
    - Implement priority logic (CLI overrides env vars)
    - Add release_id parameter (required)
    - Add auto_create_test_sets parameter (optional, default: true)
    - _Requirements: 2.1-2.11_
  
  - [x] 2.2 Implement configuration validation
    - Validate required parameters are present
    - Validate URL format for Spira instance
    - Validate file paths exist
    - Raise ConfigurationError with descriptive messages for missing/invalid config
    - _Requirements: 2.11_
  
  - [x] 2.3 Implement credential masking for logging
    - Mask API key values (show only first 4 characters)
    - Ensure no sensitive values in logs
    - _Requirements: 3.3, 3.4_
  
  - [ ]* 2.4 Write unit tests for Configuration Manager
    - Test CLI argument parsing
    - Test environment variable loading
    - Test priority rules (CLI over env)
    - Test validation error cases
    - Test credential masking
    - _Requirements: 2.1-2.9, 3.3-3.4_

- [x] 3. Implement Parser Factory and result type detection
  - [x] 3.1 Create ParserFactory class
    - Implement get_parser() method to instantiate parsers by type
    - Implement detect_result_type() for auto-detection from file extension and content
    - Implement list_supported_types() method
    - _Requirements: 4.1-4.3, 5.1-5.4_
  
  - [x] 3.2 Implement result type detection logic
    - Check file extension (.xml → junit-xml, .json → allure-json)
    - Inspect file content for ambiguous cases (XML root element, JSON structure)
    - Raise UnsupportedFormatError with supported formats list
    - _Requirements: 4.1-4.3_
  
  - [ ]* 3.3 Write unit tests for Parser Factory
    - Test parser instantiation for each supported type
    - Test auto-detection from file extensions
    - Test auto-detection from file content
    - Test error handling for unsupported formats
    - _Requirements: 4.1-4.3, 5.1-5.4_

- [x] 4. Implement JUnit XML Parser
  - [x] 4.1 Create JUnitParser class implementing TestResultParser interface
    - Implement parse() method using xml.etree.ElementTree
    - Handle both single testsuite and multiple testsuites root elements
    - Extract test case name, status, duration, timestamps
    - Extract error messages from failure/error elements
    - Map status to TestStatus enum (pass/fail/skip)
    - _Requirements: 7.1-7.7_
  
  - [x] 4.2 Implement evidence file extraction from JUnit XML
    - Parse system-out and system-err for EVIDENCE: patterns
    - Extract file paths from custom patterns
    - _Requirements: 7.7, 9.4_
  
  - [x] 4.3 Implement format validation for JUnit XML
    - Validate XML structure
    - Raise descriptive error for invalid XML
    - _Requirements: 7.2_
  
  - [ ]* 4.4 Write unit tests for JUnit Parser
    - Test parsing valid JUnit XML files
    - Test TestNG-compatible XML format
    - Test status mapping (pass/fail/skip)
    - Test error message extraction
    - Test evidence file extraction
    - Test invalid XML error handling
    - _Requirements: 7.1-7.7_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Allure JSON Parser
  - [x] 6.1 Create AllureParser class implementing TestResultParser interface
    - Implement parse() method using json module
    - Extract test case name from Allure result object
    - Extract status from status field and map to TestStatus enum
    - Extract timestamps from start and stop fields
    - Extract error messages and stack traces from statusDetails
    - _Requirements: 6.1-6.7_
  
  - [x] 6.2 Implement evidence file extraction from Allure JSON
    - Parse attachments array
    - Extract file paths from attachments[].source
    - Resolve relative paths against results directory
    - Support PNG, JPEG, MP4 file types
    - _Requirements: 6.6, 9.4_
  
  - [x] 6.3 Implement format validation for Allure JSON
    - Validate JSON structure
    - Raise descriptive error for invalid JSON
    - _Requirements: 6.2_
  
  - [ ]* 6.4 Write unit tests for Allure Parser
    - Test parsing valid Allure JSON files
    - Test status mapping (passed/failed/broken/skipped)
    - Test timestamp extraction
    - Test error message and stack trace extraction
    - Test evidence file extraction from attachments
    - Test invalid JSON error handling
    - _Requirements: 6.1-6.7_

- [ ] 7. Implement Test Case Mapper
  - [ ] 7.1 Create TestCaseMapper class
    - Implement load_mappings() to read JSON mapping file
    - Implement get_test_case_id() with exact and regex matching
    - Support exact match and regex pattern matching
    - Log warning when no mapping found
    - _Requirements: 10.1-10.4_
  
  - [ ]* 7.2 Write unit tests for Test Case Mapper
    - Test exact name matching
    - Test regex pattern matching
    - Test mapping priority (exact before regex)
    - Test warning logging for unmapped tests
    - Test loading mappings from JSON file
    - _Requirements: 10.1-10.4_

- [ ] 8. Implement Spira API Client core functionality
  - [ ] 8.1 Create SpiraAPIClient class with authentication
    - Implement __init__ with base_url, username, api_key
    - Implement authenticate() using HTTP Basic Auth
    - Validate Spira URL format
    - Cache authentication state
    - Raise error with HTTP status and message on auth failure
    - _Requirements: 11.1-11.4_
  
  - [ ] 8.2 Implement validate_release() method
    - Build GET request to /projects/{project_id}/releases/{release_id}
    - Verify release exists in project
    - Raise error with descriptive message if release not found
    - Log release name on success
    - _Requirements: 12b.1-12b.4_
  
  - [ ] 8.3 Implement create_or_get_test_set() method
    - Build GET request to /projects/{project_id}/test-sets/{test_set_id}
    - If test set exists, return test_set_id
    - If test set does not exist and auto_create_test_sets is true, create it
    - Build POST request to /projects/{project_id}/test-sets
    - Include release_id if configured
    - Parse response and extract test set ID
    - Raise error if auto_create_test_sets is false and test set doesn't exist
    - Log test set ID on success
    - _Requirements: 12a.1-12a.6_
  
  - [ ] 8.4 Implement create_test_run() method
    - Build POST request to /projects/{project_id}/test-runs/record
    - Include test case ID, execution status, timestamps, error message
    - Include release_id if configured
    - Set Content-Type: application/json
    - Parse response and extract test run ID
    - Raise error with HTTP status on API failure
    - Log test run ID on success
    - _Requirements: 12.1-12.7_
  
  - [ ]* 8.5 Write unit tests for Spira API Client (using mocks)
    - Test authentication with valid credentials
    - Test authentication failure handling
    - Test release validation
    - Test test set creation and retrieval
    - Test create_test_run with valid data
    - Test API error response handling
    - Test URL validation
    - _Requirements: 11.1-11.4, 12.1-12.7, 12a.1-12a.6, 12b.1-12b.4_

- [ ] 9. Implement Rate Limit Handler
  - [ ] 9.1 Add rate limiting logic to Spira API Client
    - Detect HTTP 429 responses
    - Implement exponential backoff (1s, 2s, 4s)
    - Retry up to 3 times
    - Log retry attempts
    - Raise error after max retries exhausted
    - _Requirements: 14.1-14.3_
  
  - [ ]* 9.2 Write unit tests for rate limit handling
    - Test retry logic with HTTP 429 responses
    - Test exponential backoff timing
    - Test max retry limit
    - Test error after exhausted retries
    - _Requirements: 14.1-14.3_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement Evidence Upload Handler
  - [ ] 11.1 Implement upload_evidence() method in SpiraAPIClient
    - Build POST request to /test-runs/{test_run_id}/attachments
    - Read file in binary mode
    - Set Content-Type: multipart/form-data
    - Preserve original filename
    - Support MIME types: image/png, image/jpeg, video/mp4, text/plain
    - _Requirements: 13.1-13.5_
  
  - [ ] 11.2 Implement evidence upload error handling
    - Validate file existence before upload
    - Log warning if file doesn't exist (don't fail execution)
    - Log error if upload fails (continue with other files)
    - Track upload success/failure counts
    - _Requirements: 13.3-13.4_
  
  - [ ]* 11.3 Write unit tests for evidence upload
    - Test successful file upload
    - Test missing file warning
    - Test upload failure handling
    - Test MIME type handling
    - Test filename preservation
    - _Requirements: 13.1-13.5_

- [ ] 12. Implement Main Orchestrator
  - [ ] 12.1 Create main execution flow
    - Initialize ConfigurationManager and load config
    - Initialize ParserFactory and get appropriate parser
    - Parse test results file
    - Initialize TestCaseMapper and load mappings
    - Initialize SpiraAPIClient
    - Iterate through test results and create test runs
    - Upload evidence files for each test run
    - Generate execution summary
    - _Requirements: 1.1-1.5, 9.1-9.5, 15.1-15.5_
  
  - [ ] 12.2 Implement execution summary generation
    - Track total tests processed
    - Track successful/failed uploads
    - Track skipped tests (no mapping)
    - Track evidence upload counts
    - Track execution duration
    - Log summary to stdout
    - _Requirements: 15.1-15.5_
  
  - [ ] 12.3 Implement error handling and exit codes
    - Catch all exceptions in main()
    - Log errors to stderr
    - Return exit code 0 on success
    - Return non-zero exit code on failure
    - Ensure partial failures don't prevent summary
    - _Requirements: 1.2-1.3, 1.5_
  
  - [ ]* 12.4 Write integration tests for main orchestrator
    - Test end-to-end flow with mock Spira API
    - Test error handling and exit codes
    - Test execution summary generation
    - Test partial failure scenarios
    - _Requirements: 1.1-1.5, 15.1-15.5_

- [ ] 13. Implement CLI entry point
  - [ ] 13.1 Create CLI script with argument definitions
    - Define all CLI arguments (spira-url, project-id, test-set-id, username, api-key, results-file, result-type, mapping-file)
    - Add help text for each argument
    - Wire CLI to main orchestrator
    - _Requirements: 1.1, 2.1-2.8_
  
  - [ ] 13.2 Add logging configuration
    - Configure logging to stdout for progress
    - Configure logging to stderr for errors
    - Set appropriate log levels
    - _Requirements: 1.4-1.5_

- [ ] 14. Create Cucumber BDD tests for the tool
  - [ ] 14.1 Create Cucumber feature files
    - Write feature for configuration loading (CLI and env vars)
    - Write feature for test result parsing (JUnit and Allure)
    - Write feature for Spira API communication
    - Write feature for error handling
    - _Requirements: 16.1, 16.3-16.6_
  
  - [ ] 14.2 Implement Cucumber step definitions
    - Implement steps for configuration scenarios
    - Implement steps for parsing scenarios
    - Implement steps for API communication (with mocks)
    - Implement steps for error handling scenarios
    - _Requirements: 16.2-16.6_
  
  - [ ]* 14.3 Run Cucumber tests and verify
    - Execute Cucumber test suite
    - Verify all scenarios pass
    - _Requirements: 16.1-16.6_

- [ ] 15. Final checkpoint and documentation
  - [ ] 15.1 Create README with usage instructions
    - Document CLI arguments and environment variables
    - Provide example commands for different CI/CD platforms
    - Document mapping file format
    - Include troubleshooting section
  
  - [ ] 15.2 Create example configuration files
    - Create example mapping file (JSON)
    - Create example JUnit XML test result
    - Create example Allure JSON test result
  
  - [ ] 15.3 Final checkpoint - Ensure all tests pass
    - Run full test suite (unit tests, integration tests, Cucumber tests)
    - Verify exit codes and error handling
    - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Automatic TC Matching via Spira Custom Property
  - [x] 16.1 Implement Spira custom property lookup for test case matching
    - Extract stable test identifier from results (Allure `testCaseId` hash, JUnit classname.name, etc.)
    - Query Spira for Test Cases where custom property `AutomationTestCaseId` matches the identifier
    - If match found, use that TC ID for the test run
    - If no match found and auto-create enabled, create TC and set the custom property
    - This replaces the need for TC IDs embedded in test names or local mapping files
    - _Prerequisite: Custom property `AutomationTestCaseId` (text) configured on Test Case artifact in Spira_
  
  - [x] 16.2 Implement Spira test case search by custom property
    - Build GET request to search test cases with filter on custom property value
    - Handle pagination if project has many test cases
    - Cache results per run to avoid repeated API calls for the same identifier
    - Fall back to name-based matching if custom property not configured
  
  - [x] 16.3 Update auto-create to populate custom property
    - When creating a new test case, include the automation identifier as the custom property value
    - Ensure subsequent runs can find the TC via the custom property lookup
    - Support configurable custom property field name via env var (SPIRA_AUTOMATION_ID_FIELD)

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation uses Python with standard libraries (xml.etree.ElementTree, json, argparse) and external dependencies (requests for HTTP, pytest for testing, cucumber for BDD)
- Checkpoints ensure incremental validation at key milestones
- Evidence upload failures are non-fatal to ensure pipeline reliability
- All sensitive credentials are externalized and masked in logs
