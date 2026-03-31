# Spira Universal Reporter — Release Overview

## Repository

https://github.com/dermotcanniffe/SpiraUniversalReporter

## What It Is

A Python CLI tool that bridges CI/CD test automation with Spira test management. It parses test results from automated test frameworks, matches them to Spira test cases, creates test runs with full execution details, and uploads evidence files — all without requiring changes to the client's test code.

The tool is designed to be injected as a post-test pipeline stage. The client only needs to configure environment variables in their CI/CD YAML.

## Core Capabilities

### Test Result Parsing
- Allure JSON (Cypress, Playwright, pytest) — names, statuses, timestamps, errors, stack traces, evidence from nested step attachments
- JUnit XML (TestNG, Maven Surefire, Gradle) — names, statuses, durations, errors, evidence from EVIDENCE: patterns
- ExtentReports HTML (Selenium, custom Java frameworks) — parses Summary.html, discovers screenshots and consolidated docs from per-test directories
- Pluggable architecture — new formats added by subclassing TestResultParser with format_name and can_parse(), no core code changes needed

### Test Case Matching
- Stateless matching via Spira custom properties — extracts a stable automation ID from each test result (Allure content hash, JUnit classname.name, ExtentReports test name), searches Spira for a matching TC, reuses if found, auto-creates if not
- Regex fallback — extracts numeric TC IDs from test names ([TC:123], TC-123, etc.)
- No local mapping files, no repo commits, no test code modifications required

### Spira Integration
- Authentication with username + API key
- Release validation (fails gracefully if release doesn't exist)
- Test set management (optional — checks/creates test sets, fetches TC mappings for proper linkage)
- Test run creation with status mapping, timestamps, error messages, stack traces
- Evidence upload (screenshots, videos, logs) as base64-encoded attachments
- Exponential backoff retry on HTTP 429 rate limiting (1s, 2s, 4s, max 3 retries)

### CLI Modes
- `spira-report [path]` — full run with auto-sense result discovery
- `spira-report --preflight` — validate config and connectivity without sending results
- `spira-report --help` — usage reference with all environment variables
- Results path resolution: CLI arg > SPIRA_RESULTS_DIR env var > current working directory
- Pip-installable with `spira-report` console script entry point

## Test Coverage

13 BDD features, 97 scenarios, 398 steps — all passing.

- Offline tests: parser logic, config validation, TC ID extraction, auto-sense discovery, CLI modes
- Integration tests (@integration): real Spira API calls — authentication, release validation, test run creation, evidence upload, custom property search/create
- Integration tests reuse TCs via stable automation IDs and clean up temporary artifacts

## Known Limitations

- Test set linkage requires TCs to be pre-added to the test set in Spira (REST API does not expose an endpoint to add TCs to test sets programmatically). The tool logs a warning with a direct Spira link when a TC isn't in the specified test set.
- SPIRA_TEST_SET_ID is optional. Test runs are created regardless — they just won't be grouped under a test set if the TC isn't a member.
- JUnit/TestNG TC mapping uses classname.name as the automation ID, which is less stable than Allure's content-based hash.

## Pipeline Integration

Minimal client effort — add two lines to the pipeline YAML:

```yaml
script:
  - pip install git+https://github.com/dermotcanniffe/SpiraUniversalReporter.git
  - spira-report
```

All configuration via environment variables. Sensitive values (username, API key) stored in the platform's secrets manager. See docs/ci-cd-integration.md for GitLab, GitHub Actions, Jenkins, and Azure DevOps examples.

## Documentation

| Document | Description |
|----------|-------------|
| [README](README.md) | Landing page with quick start |
| [Getting Started](docs/getting-started.md) | Installation, first run, BDD tests |
| [Configuration](docs/configuration.md) | All environment variables |
| [CI/CD Integration](docs/ci-cd-integration.md) | Pipeline examples for 4 platforms |
| [Parsers](docs/parsers.md) | Supported formats, field extraction, custom parser guide |
| [TC Matching](docs/tc-matching.md) | Custom property flow, regex fallback, test set linkage |
| [Architecture](docs/architecture.md) | Project structure, components, data flow |
| [Examples README](examples/README.md) | Sample data directory guide |

## Technology

- Python 3.9+
- Dependencies: requests, beautifulsoup4
- Test framework: Behave (BDD/Cucumber)
- Package: pip-installable via pyproject.toml
