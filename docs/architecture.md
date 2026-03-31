# Architecture

## Project Structure

```
src/spira_integration/
├── cli.py                        # CLI entry point (spira-report command)
├── api/
│   └── spira_client.py           # Spira REST API client
├── config/
│   └── config_manager.py         # Configuration management
├── mapper/
│   └── test_case_mapper.py       # TC ID extraction and automation ID mapping
├── parsers/
│   ├── allure_parser.py          # Allure JSON parser
│   ├── extent_parser.py          # ExtentReports HTML parser
│   ├── junit_parser.py           # JUnit XML parser
│   ├── parser_factory.py         # Plugin registry and auto-detection
│   └── sample_custom_parser.py   # Template for custom parsers
├── parser_base.py                # Abstract base class for parsers
├── models.py                     # Data models (TestResult, TestStatus, Configuration, etc.)
├── exceptions.py                 # Custom exceptions
└── logging_config.py             # Logging setup
```

## Key Components

### CLI (`cli.py`)

Three modes:
- `spira-report [path]` — full run: parse, match, create runs, upload evidence
- `spira-report --preflight` — validate config and connectivity
- `spira-report --help` — usage reference

Auto-sense discovery scans the resolved path using each registered parser's `can_parse()`.

### Parser Factory (`parsers/parser_factory.py`)

Plugin registry pattern. Parsers self-register with `format_name` and `can_parse()`. The factory:
- Auto-registers built-in parsers on first use
- Supports `register(ParserClass)` for runtime registration
- Supports `load_custom_parsers(directory)` for file-based discovery
- Iterates parsers for format auto-detection

### Parser Base Class (`parser_base.py`)

All parsers subclass `TestResultParser`:

```python
class MyParser(TestResultParser):
    format_name = 'my-format'

    def can_parse(self, file_path: str) -> bool:
        # Return True if this parser handles the input
        ...

    def parse(self, file_path: str) -> List[TestResult]:
        # Parse and return TestResult objects
        ...
```

### Spira API Client (`api/spira_client.py`)

Handles all Spira REST API communication:
- Authentication (username + API key)
- Release validation
- Test set management (check/create, get TC mappings)
- Test case search by custom property
- Test case creation (with or without custom properties)
- Test run creation (with optional test set linkage via TestSetTestCaseId)
- Evidence upload (base64-encoded file attachments)
- Test case deletion (for test cleanup)

### Test Case Mapper (`mapper/test_case_mapper.py`)

Two extraction strategies:
- `extract_automation_id(raw_data)` — stable ID for custom property matching
- `extract_test_case_id(raw_data)` / `get_test_case_id(name)` — numeric TC ID from regex patterns

## Data Flow

```
Environment Variables
        ↓
    CLI (cli.py)
        ↓
    ParserFactory.detect_result_type()
        ↓
    Parser.parse() → List[TestResult]
        ↓
    TestCaseMapper.extract_automation_id()
        ↓
    SpiraAPIClient.search_test_case_by_custom_property()
        ↓ (found or created)
    SpiraAPIClient.create_test_run()
        ↓
    SpiraAPIClient.upload_evidence()
        ↓
    Execution Summary
```

## Testing

13 BDD features, 96 scenarios, 394 steps using Behave.

- Offline tests: parser logic, config validation, TC ID extraction, auto-sense discovery
- Integration tests (`@integration` tag): real Spira API calls — auth, release validation, test run creation, evidence upload, custom property search/create
- Integration tests reuse TCs via stable automation IDs and clean up temporary artifacts
