# Getting Started

## Installation

### From a zip/tarball (no Git access)

Extract the archive and install from the local directory:

```bash
cd SpiraUniversalReporter
pip install .
```

This installs the `spira-report` command. To verify:

```bash
spira-report --help
```

### Without installing

If you can't install packages, run directly from the `src/` directory:

```bash
cd SpiraUniversalReporter/src
python -m spira_integration.cli --help
```

This works identically to `spira-report` — just a longer command.

### From Git (if available)

```bash
pip install git+https://github.com/dermotcanniffe/SpiraUniversalReporter.git
```

### Development (includes test dependencies)

```bash
pip install -e ".[dev]"
```

## Publishing to Internal Artifactory

To host the package on an internal Python package repository (Artifactory, Nexus, etc.):

```bash
# Build the wheel
pip install build
python -m build
```

This produces `dist/spira_test_reporter-0.1.0-py3-none-any.whl`. Upload that to your internal repository, then install from there:

```bash
pip install spira-test-reporter --index-url https://artifactory.internal/api/pypi/simple/
```

In a GitLab pipeline:

```yaml
script:
  - pip install spira-test-reporter --index-url $PIP_INDEX_URL
  - spira-report
```

## First Run

### 1. Configure credentials

Set environment variables directly, or copy `.env.example` to `.env` for local testing:

```bash
cp .env.example .env
```

See [Configuration](configuration.md) for all options. At minimum you need:

```bash
SPIRA_URL=https://your-company.spiraservice.net
SPIRA_USERNAME=your_username
SPIRA_API_KEY={your-api-key}
SPIRA_PROJECT_ID=1
SPIRA_RELEASE_ID=5
```

### 2. Validate your setup

```bash
spira-report --preflight
```

This checks:
- All required env vars are set
- Spira authentication succeeds
- Configured release exists
- Configured test set exists (if specified)

### 3. Run against test results

```bash
# With spira-report installed
spira-report ./path/to/results/

# Or without installing
python -m spira_integration.cli --results-file ./path/to/results/

# Or with all config as CLI args
spira-report --url https://spira.company.net --project-id 25 --release-id 155 \
             --username user@company.com --api-key "{key}" \
             --results-file ./target/surefire-reports
```

The tool auto-detects the format, parses results, matches to Spira test cases, creates test runs, and uploads evidence.

## Running BDD Tests

```bash
# All tests (requires Spira connectivity for @integration tests)
behave

# Offline tests only
behave --tags="~@integration"

# Integration tests only (hits real Spira)
behave --tags="@integration"
```

The integration tests reuse test cases via custom property matching and clean up after themselves.
