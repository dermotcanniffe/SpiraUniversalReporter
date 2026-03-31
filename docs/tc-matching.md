# Test Case Matching

The tool matches test results to Spira test cases using two strategies.

## Custom Property Matching (Recommended)

When `SPIRA_AUTOMATION_ID_FIELD` is set, the tool uses a stable identifier from the test result to find or create the corresponding Spira test case.

### How It Works

1. Extract a stable automation ID from the test result:
   - Allure: `testCaseId` field (content-based hash, e.g. `e82fecfb3ac31d524a5d9c18c7cec49e`)
   - JUnit: `classname.name` composite (e.g. `com.example.LoginTest.testLogin`)
   - ExtentReports: test name (e.g. `Web_TC01`)

2. Search Spira for a test case where the custom property matches that ID

3. If found — reuse that test case for the new test run

4. If not found and `SPIRA_AUTO_CREATE_TEST_CASES=true` — create a new test case with the automation ID stored in the custom property

5. If not found and auto-create is disabled — skip the test result and log a warning

### Setup

1. In Spira, create a custom text property on the Test Case artifact (e.g. `Custom_04`)
2. Set `SPIRA_AUTOMATION_ID_FIELD=Custom_04` in your environment

The identifier only changes if the test itself changes (renamed scenario, moved class, etc.). Repeated pipeline runs reuse the same test case — no duplicates.

## TC ID Regex Extraction (Fallback)

When `SPIRA_AUTOMATION_ID_FIELD` is not set, the tool falls back to extracting numeric Spira TC IDs from test names:

| Pattern | Example |
|---------|---------|
| `[TC:123]` | `User can login [TC:123]` |
| `TC-123:` | `TC-123: Login test` |
| `(TC:123)` | `Login test (TC:123)` |
| `TC123` | `TC123 validation` |

Also checks Allure labels (`testCaseId`), `fullName`, and `description` fields.

## Test Set Linkage

`SPIRA_TEST_SET_ID` is optional. When specified:

- The tool fetches the test set's existing TC-to-test-set mappings at startup
- If a TC is already in the test set, the test run is linked to it via `TestSetTestCaseId`
- If a TC is not in the test set, the test run is still created but not linked. A warning is logged with a direct Spira link:

```
⚠ TC:729 is not in Test Set 50. Run created but not linked to test set.
  Add it: https://your-company.spiraservice.net/1/TestSet/50.aspx
```

This is a Spira REST API limitation — there is no documented endpoint to programmatically add a test case to a test set. TCs must be added to the test set manually in Spira before they can be linked to test runs.

When `SPIRA_TEST_SET_ID` is not set, test runs are created against test cases directly. They appear in the test case's execution history and the project-level test runs list.
