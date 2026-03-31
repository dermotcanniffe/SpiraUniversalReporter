# Configuration

All configuration is via environment variables. For local development, create a `.env` file from `.env.example`.

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
