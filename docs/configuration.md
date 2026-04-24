# Configuration

Configuration can be provided via CLI arguments, environment variables, or a `.env` file. Priority: CLI args > env vars > .env file.

## CLI Arguments

All environment variables can also be passed as CLI arguments:

```bash
spira-report --url https://company.spiraservice.net \
             --username user@company.com \
             --api-key "{00000000-0000-0000-0000-000000000000}" \
             --project-id 25 \
             --release-id 155 \
             --results-file ./target/surefire-reports
```

| CLI Argument | Env Variable | Description |
|-------------|-------------|-------------|
| `--url` | `SPIRA_URL` | Spira instance URL (required) |
| `--username` | `SPIRA_USERNAME` | Spira username (required) |
| `--api-key` | `SPIRA_API_KEY` | Spira API key with curly braces (required) |
| `--project-id` | `SPIRA_PROJECT_ID` | Spira project ID (required) |
| `--release-id` | `SPIRA_RELEASE_ID` | Spira release ID (required) |
| `--test-set-id` | `SPIRA_TEST_SET_ID` | Spira test set ID (optional) |
| `--results-file` | `SPIRA_RESULTS_DIR` | Path to test results file or directory |
| `--results-dir` | `SPIRA_RESULTS_DIR` | Same as above (alias) |
| `--result-type` | `SPIRA_RESULT_TYPE` | Override format detection |
| `--automation-id-field` | `SPIRA_AUTOMATION_ID_FIELD` | Custom property for TC matching |
| `--ssl-verify` | `SPIRA_SSL_VERIFY` | SSL verification (default: `true`) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SPIRA_URL` | Yes | Spira instance URL (e.g. `https://company.spiraservice.net`) |
| `SPIRA_USERNAME` | Yes | Spira username |
| `SPIRA_API_KEY` | Yes | Spira API key (include curly braces) |
| `SPIRA_PROJECT_ID` | Yes | Spira project ID |
| `SPIRA_RELEASE_ID` | Yes | Spira release ID (validated, not auto-created) |
| `SPIRA_TEST_SET_ID` | No | Spira test set ID (optional, see [Test Case Matching](tc-matching.md)) |
| `SPIRA_RESULTS_DIR` | No | Path to scan for test results (or pass as CLI arg) |
| `SPIRA_RESULT_TYPE` | No | Override format auto-detection (`junit-xml`, `allure-json`, `extent-html`) |
| `SPIRA_AUTOMATION_ID_FIELD` | No | Custom property field for TC matching (e.g. `Custom_04`) |
| `SPIRA_AUTO_CREATE_TEST_CASES` | No | Auto-create missing test cases (default: `true`) |
| `SPIRA_AUTO_CREATE_TEST_SETS` | No | Auto-create missing test sets (default: `true`) |
| `SPIRA_SSL_VERIFY` | No | SSL certificate verification (default: `true`). Set to `false` for corporate/internal certs |

## Results Path Resolution

The tool resolves where to scan for test results in this order:

1. Positional CLI argument: `spira-report ./path/`
2. `SPIRA_RESULTS_DIR` environment variable
3. Current working directory

## Getting Your Spira API Key

1. Log into your Spira instance
2. Go to your user profile (top right)
3. Navigate to "RSS Tokens" or "API Keys"
4. Copy your API key — include the curly braces: `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}`

## Security

- Never commit `.env` to version control (already in `.gitignore`)
- API keys are masked in logs (only first 4 characters shown)
- In CI/CD pipelines, use your platform's secrets manager for `SPIRA_USERNAME` and `SPIRA_API_KEY`

## SSL Certificate Verification

The tool verifies SSL certificates by default using Python's built-in CA bundle. For corporate environments with internal certificate authorities, there are three options (in order of preference):

### Option 1: Use OS certificate store (recommended)

Install `truststore` to make Python trust the same certificates as your OS. If your corporate CA is trusted by Windows/macOS/Linux, Python will trust it too — no config needed.

```bash
pip install truststore
```

The tool detects `truststore` automatically at startup. Nothing else to configure.

### Option 2: Point to a custom CA bundle

Set `SPIRA_SSL_VERIFY` to the path of your corporate CA certificate file (.pem):

```bash
SPIRA_SSL_VERIFY=/path/to/corporate-ca-bundle.pem
# or
spira-report --ssl-verify /path/to/corporate-ca-bundle.pem
```

### Option 3: Disable verification (not recommended)

As a last resort, disable SSL verification entirely:

```bash
SPIRA_SSL_VERIFY=false
```

A warning is logged when verification is disabled.
