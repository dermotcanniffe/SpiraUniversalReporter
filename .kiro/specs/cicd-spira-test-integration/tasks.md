# Implementation Plan: CI/CD Spira Test Integration

## Overview

Python-based CLI tool (`spira-report`) that parses test results from CI/CD pipelines and transmits them to Spira via REST API. Pluggable parser architecture, stateless TC matching via custom properties, auto-sense result discovery.

## Tasks

- [x] 1. Project structure and core interfaces
  - Python package structure, data models, TestResultParser base class, logging, requirements.txt
  - _Requirements: 1.1, 1.4, 2.1-2.8, 3.1-3.4_

- [x] 2. Configuration Manager
  - CLI argument and env var loading with priority logic, validation, credential masking
  - release_id (required), test_set_id (optional), auto_create_test_sets, automation_id_field
  - _Requirements: 2.1-2.11, 3.3-3.4_

- [x] 3. Parser Factory with plugin registry
  - ParserFactory with register(), load_custom_parsers(), detect_result_type() via can_parse()
  - Built-in parsers auto-registered, custom parsers discoverable from directory
  - _Requirements: 4.1-4.3, 5.1-5.4, 18.1-18.7_

- [x] 4. JUnit XML Parser
  - Parses testsuite/testsuites, extracts status/duration/timestamps/errors, EVIDENCE: patterns
  - format_name='junit-xml', can_parse() checks .xml extension and root element
  - _Requirements: 7.1-7.7_

- [x] 5. Allure JSON Parser
  - Parses uuid/status/start/stop/statusDetails/attachments, recursive step walking for evidence
  - format_name='allure-json', can_parse() checks .json with uuid+status fields
  - _Requirements: 6.1-6.7_

- [x] 6. ExtentReports HTML Parser
  - Parses Summary.html (up to 2 levels deep), extracts test names/statuses/timestamps/durations/errors
  - Discovers screenshots and consolidated docs from per-test directories
  - format_name='extent-html', can_parse() checks for Summary.html in directory
  - _Requirements: 17.1-17.9_

- [x] 7. Test Case Mapper
  - extract_test_case_id() with regex patterns: [TC:123], TC-123, (TC:123), TC123
  - extract_automation_id() for Allure testCaseId hash, JUnit classname.name
  - _Requirements: 10.1-10.4, 19.1-19.10_

- [x] 8. Spira API Client
  - authenticate(), validate_release(), create_or_get_test_set()
  - create_test_run() with optional test_set_id and test_set_test_case_id
  - create_test_case(), create_test_case_with_custom_property()
  - search_test_case_by_custom_property() with pagination
  - upload_evidence() with base64 encoding
  - get_test_set_tc_mappings(), delete_test_case()
  - _request_with_retry() for exponential backoff on 429
  - _Requirements: 11.1-11.4, 12.1-12.7, 12a.1-12a.6, 12b.1-12b.4, 13.1-13.5, 14.1-14.3_

- [x] 9. CLI Entry Point (spira-report)
  - Three modes: full run, --preflight, --help
  - Auto-sense discovery via can_parse() on resolved path
  - Results path resolution: CLI arg > SPIRA_RESULTS_DIR > cwd
  - Full orchestration: parse → match → create runs → upload evidence → summary
  - pip-installable via pyproject.toml with console_scripts entry point
  - _Requirements: 1.1-1.5, 15.1-15.5, 20.1-20.10, 21.1-21.6_

- [x] 10. Stateless TC Matching via Custom Properties
  - Search Spira by custom property value, auto-create with property if not found
  - Configurable field name via SPIRA_AUTOMATION_ID_FIELD
  - Fallback to regex TC ID extraction from test names
  - _Requirements: 19.1-19.10_

- [x] 11. BDD Test Suite
  - 13 features, 97 scenarios, 398 steps
  - Offline tests: parsers, config, mapper, auto-sense, CLI modes
  - Integration tests (@integration): real Spira API — auth, release, test runs, evidence, custom properties
  - Integration tests reuse TCs via stable automation IDs, clean up after themselves
  - _Requirements: 16.1-16.6_

- [x] 12. Documentation
  - README with Mermaid diagram and doc links
  - docs/: getting-started, configuration, ci-cd-integration, parsers, tc-matching, architecture
  - examples/README.md documenting sample data
  - sample_custom_parser.py with step-by-step instructions

## Known Limitations

- Test set linkage requires TCs to be pre-added to the test set in Spira (REST API limitation)
- SPIRA_TEST_SET_ID is optional; test runs created regardless but not grouped if TC not in test set
- JUnit/TestNG TC mapping uses classname.name which is less stable than Allure's content hash
