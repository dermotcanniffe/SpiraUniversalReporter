# Examples Directory

Sample and client-provided test result data used for development, testing, and demos.

## Contents

### sample-allure-results.json

Synthetic Allure JSON test results. Used by:
- BDD tests (`features/06_allure_parser.feature`, `features/12_preflight_validation.feature`)
- Demo script (`demo_end_to_end.py`)

Contains test results with TC IDs embedded in names (e.g. `[TC:707]`), various pass/fail statuses, and attachment references. This is generated data, not from a real test run.

### sample-junit-results.xml

Synthetic JUnit XML test results. Used by:
- BDD tests (`features/04_junit_parser.feature`, `features/12_preflight_validation.feature`)

Contains a TestNG-compatible testsuite with passing, failing, and skipped tests, error messages, stack traces, and EVIDENCE: patterns in system-out. This is generated data.

### client-report/

Real Allure results from a client's Cypress + Cucumber BDD test suite. Contains:
- `allure-results/` — Individual test result JSON files and container files
- `allure-results/*.png` — Screenshot attachments
- `allure-results/*.mp4` — Video attachments
- `allure-report/` — Generated Allure HTML report

Key characteristics:
- Uses `@badeball/cypress-cucumber-preprocessor` (Cypress + Cucumber)
- `testCaseId` field contains Allure's content-based hash (stable across runs)
- Attachments are nested inside steps, not at the top level
- No Spira TC IDs in test names — relies on custom property matching

### client-testng-results/

Real results from a client's Selenium + TestNG framework using ExtentReports. Contains:
- `Result/Report_<timestamp>/Summary.html` — Main summary report (parsed by ExtentParser)
- `Result/Report_<timestamp>/<TestName>_<timestamp>/` — Per-test-case directories with:
  - `Screenshots/` — Step-level screenshots (PNG)
  - `ConsolidatedScreenshots/` — Combined screenshot documents (DOCX)
  - `HTML Reporting/Report.html` — Individual test detail report
- `Result/Report_<timestamp>/excel_Report.xlsx` — Excel summary
- `Result/Report_<timestamp>/<TestName>_<timestamp>.zip` — Archived test results

Key characteristics:
- ExtentReports v3 HTML output (not JUnit XML or TestNG XML)
- Test names like `Web_TC01`, `Web_TC02` used as automation IDs
- Screenshots captured per step with numbered filenames

## Test Case Mapping by Format

| Format | Automation ID (custom property mode) | Fallback (regex from name) |
|--------|--------------------------------------|---------------------------|
| Allure JSON | `testCaseId` field (content hash) | `[TC:123]` in name/fullName/description |
| JUnit XML | `classname.name` composite | `[TC:123]` in test name |
| ExtentReports | Test name from HTML node | `[TC:123]` in test name |

## Adding New Sample Data

To test with new result formats or client data:
1. Create a new subdirectory (e.g. `examples/client-nunit-results/`)
2. Copy the test result files into it
3. Update `SPIRA_RESULTS_FILE` in `.env` to point at the new directory/file
4. Run `behave features/12_preflight_validation.feature` to verify parsing works
