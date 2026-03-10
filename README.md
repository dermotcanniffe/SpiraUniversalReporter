# Spira CI/CD Test Integration

Python-based CLI tool that parses test results from CI/CD pipelines and transmits them to Spira test management system via REST API.

## Features

- **Automatic Format Detection** - Detects JUnit XML or Allure JSON automatically
- **Smart Test Case Mapping** - Extracts TC IDs from test names (no mapping files needed)
- **Auto-Create Test Cases** - Creates missing test cases in Spira automatically
- **Parse Multiple Formats** - JUnit XML (TestNG) and Allure JSON (Cypress)
- **Send Results to Spira** - Creates test runs via REST API with full details
- **Attach Evidence Files** - Screenshots, videos, logs (coming soon)
- **Secure Credentials** - CLI args or environment variables
- **CI/CD Ready** - Works in any pipeline (GitHub Actions, GitLab CI, Jenkins)

## Supported Test Result Formats

### Automatic Format Detection

The tool automatically detects the test result format using a two-step process:

1. **File Extension Check**
   - `.xml` files → Checks for JUnit XML format
   - `.json` files → Checks for Allure JSON format

2. **Content Validation**
   - **JUnit XML**: Validates root element is `<testsuite>` or `<testsuites>`
   - **Allure JSON**: Validates presence of `uuid` and `status` fields

### Supported Formats

#### Allure JSON (Cypress, Playwright, etc.)
```json
{
  "uuid": "test-uuid-1",
  "name": "User can login [TC:123]",
  "status": "passed",
  "start": 1234567890000,
  "stop": 1234567892000
}
```

**Detection criteria:**
- File extension: `.json`
- Required fields: `uuid`, `status`
- Supports both single object and array of objects

#### JUnit XML (TestNG, Maven Surefire, etc.)
```xml
<testsuite name="Test Suite">
  <testcase name="User can login [TC:123]" time="2.5">
    <failure message="Assertion failed">...</failure>
  </testcase>
</testsuite>
```

**Detection criteria:**
- File extension: `.xml`
- Root element: `<testsuite>` or `<testsuites>`

### Manual Format Override

If auto-detection fails or you want to be explicit:

```bash
# Via command line
--result-type allure-json

# Via environment variable
SPIRA_RESULT_TYPE=allure-json
```

## Test Case Mapping

### Automatic TC ID Extraction

The tool automatically extracts Spira test case IDs from test names. No mapping files needed!

**Supported formats:**
- `[TC:123]` - Recommended (clear and visible)
- `TC-123:` - Prefix style
- `(TC:123)` - Parentheses style
- `TC123` - Compact style

**Example test names:**
```json
{
  "name": "User can login successfully [TC:707]"
}
```

```xml
<testcase name="TC-708: User cannot login with invalid credentials">
```

**Also checks:**
- Allure labels: `testCaseId` label
- Test descriptions: Searches for TC patterns
- Full test names: Checks complete test path

### Auto-Create Missing Test Cases

By default, the tool creates test cases in Spira if they don't exist:

```bash
# Enable (default)
SPIRA_AUTO_CREATE_TEST_CASES=true

# Disable
SPIRA_AUTO_CREATE_TEST_CASES=false
```

When enabled:
1. Tries to create test run with specified TC ID
2. If TC doesn't exist (404 error), creates the test case automatically
3. Then creates the test run with the new TC ID
4. Logs the new TC ID for reference

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

### Setting up Spira Credentials

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your Spira instance details:
   ```bash
   SPIRA_URL=https://your-company.spiraservice.net
   SPIRA_USERNAME=your_username
   SPIRA_API_KEY={your-api-key-with-curly-braces}
   SPIRA_PROJECT_ID=1
   SPIRA_TEST_SET_ID=1
   ```

3. Get your Spira API Key:
   - Log into your Spira instance
   - Go to your user profile (top right)
   - Navigate to "RSS Tokens" or "API Keys"
   - Copy your API key (include the curly braces)

### Testing Your Connection

Run the connection test script to verify your credentials:

```bash
python test_spira_connection.py
```

This will:
- Load credentials from your `.env` file
- Initialize the Spira API client
- Test authentication
- Report success or any errors

## Usage

### Command Line

```bash
python -m spira_integration.cli \
  --url https://your-company.spiraservice.net \
  --project-id 1 \
  --test-set-id 10 \
  --username your_username \
  --api-key {your-api-key} \
  --results-file path/to/results.json \
  --result-type allure-json
```

### Using Environment Variables

Set environment variables and run with minimal arguments:

```bash
export SPIRA_URL=https://your-company.spiraservice.net
export SPIRA_USERNAME=your_username
export SPIRA_API_KEY={your-api-key}
export SPIRA_PROJECT_ID=1
export SPIRA_TEST_SET_ID=10

python -m spira_integration.cli --results-file path/to/results.json
```

### Demo Mode (Parsing Only)

Test the parser without sending to Spira:

```bash
python run_demo.py
```

This will parse the sample Allure results and display them without making API calls.

## Development

### Run BDD Tests

```bash
behave features/
```

### Run Specific Feature

```bash
behave features/08_spira_api_client.feature
```

### Project Structure

```
src/spira_integration/
├── api/
│   └── spira_client.py      # Spira REST API client
├── config/
│   └── config_manager.py    # Configuration management
├── parsers/
│   ├── allure_parser.py     # Allure JSON parser
│   ├── junit_parser.py      # JUnit XML parser
│   └── parser_factory.py    # Parser factory
├── models.py                # Data models
├── exceptions.py            # Custom exceptions
└── cli.py                   # CLI entry point
```

## Security Notes

- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- API keys are masked in logs (only first 4 characters shown)
- Use environment variables in CI/CD pipelines instead of hardcoding credentials
