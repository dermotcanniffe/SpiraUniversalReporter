# Getting Started

## Installation

```bash
# From git
pip install git+https://github.com/dermotcanniffe/SpiraUniversalReporter.git

# From local copy
pip install .

# Development (includes test dependencies)
pip install -e ".[dev]"
```

## First Run

### 1. Configure credentials

Copy `.env.example` to `.env` and fill in your Spira details:

```bash
cp .env.example .env
```

See [Configuration](configuration.md) for all available options.

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
spira-report ./path/to/results/
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
