# Spira CI/CD Test Integration

Python-based CLI tool that parses test results from CI/CD pipelines and transmits them to Spira test management system via REST API.

## Features

- Parse JUnit XML (TestNG) and Allure JSON (Cypress) test results
- Send test results to Spira via REST API
- Attach evidence files (screenshots, videos, logs)
- Secure credential management (CLI args or environment variables)
- Pluggable parser architecture

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
