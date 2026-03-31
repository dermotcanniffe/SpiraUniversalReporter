# Parsers

## Supported Formats

The tool auto-detects the format by asking each registered parser's `can_parse()` method.

| Format | Detection | Source Frameworks |
|--------|-----------|-------------------|
| Allure JSON | `.json` file with `uuid` + `status` fields | Cypress, Playwright, pytest |
| JUnit XML | `.xml` file with `<testsuite>` root element | TestNG, Maven Surefire, Gradle |
| ExtentReports HTML | Directory containing `Summary.html` | Selenium, custom Java frameworks |

## What's Extracted Per Format

### Allure JSON

| Field | Source |
|-------|--------|
| Test name | `name` or `fullName` |
| Status | `status` field (passed/failed/broken/skipped) |
| Start/end time | `start`/`stop` (milliseconds since epoch) |
| Error message | `statusDetails.message` |
| Stack trace | `statusDetails.trace` |
| Evidence files | `attachments[].source`, recursively through `steps[].steps[].attachments` |
| Automation ID | `testCaseId` (content-based hash, stable across runs) |

### JUnit XML

| Field | Source |
|-------|--------|
| Test name | `testcase` `name` attribute (prefixed with `classname` if present) |
| Status | Presence of `<failure>`, `<error>`, `<skipped>` elements |
| Duration | `time` attribute on `testcase` |
| Timestamps | `timestamp` attribute on `testsuite` |
| Error message | `message` attribute on `<failure>`/`<error>` |
| Stack trace | Text content of `<failure>`/`<error>` |
| Evidence files | `EVIDENCE:` patterns in `<system-out>`/`<system-err>` |
| Automation ID | `classname.name` composite |

### ExtentReports HTML

| Field | Source |
|-------|--------|
| Test name | `div.node-name` in `li.node.leaf` elements |
| Status | `status` attribute on `li.node` (pass/fail/fatal/error/warning/skip) |
| Start time | `span.node-time` (format: `MMM d, yyyy hh:mm:ss a`) |
| Duration | `span.node-duration` (format: `0h 0m 56s+560ms`) |
| Error message | `td.step-details` from failed step rows |
| Evidence files | `Screenshots/*.png` and `ConsolidatedScreenshots/*.docx` in per-test directories |
| Automation ID | Test name from HTML node |

## Adding a Custom Parser

The parser architecture is pluggable. To support a new format:

1. Copy `src/spira_integration/parsers/sample_custom_parser.py`
2. Set `format_name` to a unique identifier (e.g. `'nunit-xml'`)
3. Implement `can_parse(file_path)` — return `True` if the file/directory matches your format
4. Implement `parse(file_path)` — return a list of `TestResult` objects
5. Register: `ParserFactory.register(MyParser)`

The sample parser file has detailed comments and a working CSV example.

### Registration Methods

```python
# Manual registration
from spira_integration.parsers.parser_factory import ParserFactory
ParserFactory.register(MyParser)

# Auto-discovery from a directory of .py files
ParserFactory.load_custom_parsers('/path/to/custom_parsers/')
```

### TestResult Fields

Each parser returns `TestResult` objects with:

```python
TestResult(
    name='test name',              # required
    status=TestStatus.PASSED,      # required (PASSED/FAILED/SKIPPED/BLOCKED/CAUTION)
    duration=1.5,                  # seconds (optional)
    start_time=datetime(...),      # optional
    end_time=datetime(...),        # optional
    error_message='...',           # optional
    stack_trace='...',             # optional
    evidence_files=['path.png'],   # optional
    raw_data={'key': 'value'},     # optional, used for TC ID extraction
)
```
