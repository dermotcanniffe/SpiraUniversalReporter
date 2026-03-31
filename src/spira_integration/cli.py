"""
spira-report — CLI entry point for Spira test result integration.

Usage:
    spira-report [results_path]       # scan path or auto-sense from env/cwd
    spira-report --preflight          # validate config and connectivity only
    spira-report --help

All Spira config comes from environment variables (or .env file for local dev).
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from .config.config_manager import ConfigurationManager
from .parsers.parser_factory import ParserFactory
from .api.spira_client import SpiraAPIClient
from .mapper.test_case_mapper import TestCaseMapper
from .models import ExecutionSummary
from .exceptions import APIError
from .logging_config import setup_logging

logger = logging.getLogger(__name__)


def _load_env_file():
    """Load .env file if present (local dev only, CI provides env vars)."""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip()


def _resolve_results_path(cli_arg=None):
    """Resolve the results path: CLI arg > SPIRA_RESULTS_DIR > cwd."""
    if cli_arg:
        return cli_arg

    env_path = os.environ.get('SPIRA_RESULTS_DIR') or os.environ.get('SPIRA_RESULTS_FILE')
    if env_path:
        return env_path

    return '.'


def _discover_results(scan_path):
    """
    Auto-sense: scan a directory for parseable test results.
    Uses each registered parser's can_parse() to find candidates.
    """
    factory = ParserFactory()
    path = Path(scan_path)

    if not path.exists():
        logger.error(f"Results path does not exist: {scan_path}")
        return None, None

    # If it's a file, try to detect directly
    if path.is_file():
        try:
            fmt = factory.detect_result_type(str(path))
            return str(path), fmt
        except Exception:
            return None, None

    # If it's a directory, check the directory itself first
    try:
        fmt = factory.detect_result_type(str(path))
        return str(path), fmt
    except Exception:
        pass

    # Scan immediate children
    candidates = []
    for child in sorted(path.iterdir()):
        try:
            fmt = factory.detect_result_type(str(child))
            candidates.append((str(child), fmt))
        except Exception:
            continue

    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        logger.info(f"Found {len(candidates)} result sets:")
        for c, f in candidates:
            logger.info(f"  {f}: {c}")
        # Return the first one — could be smarter later
        return candidates[0]

    return None, None


def _get_env(name, required=True):
    """Get env var, fail with clear message if required and missing."""
    val = os.environ.get(name, '')
    if required and not val:
        logger.error(f"{name} is not set. Define it as an environment variable or in .env")
        sys.exit(1)
    return val


def run_preflight():
    """Validate config and connectivity without sending results."""
    print("Pre-flight validation...")
    url = _get_env('SPIRA_URL')
    username = _get_env('SPIRA_USERNAME')
    api_key = _get_env('SPIRA_API_KEY')
    project_id = int(_get_env('SPIRA_PROJECT_ID'))
    release_id = int(_get_env('SPIRA_RELEASE_ID'))
    test_set_id_str = _get_env('SPIRA_TEST_SET_ID', required=False)

    client = SpiraAPIClient(url, username, api_key)

    print(f"  Authenticating with {url}...")
    client.authenticate()
    print("  ✓ Authentication OK")

    print(f"  Validating release {release_id}...")
    release = client.validate_release(project_id, release_id)
    print(f"  ✓ Release: {release.get('Name')}")

    if test_set_id_str:
        test_set_id = int(test_set_id_str)
        print(f"  Checking test set {test_set_id}...")
        client.create_or_get_test_set(project_id, test_set_id, release_id=release_id)
        print("  ✓ Test set OK")
    else:
        print("  ○ No test set configured (SPIRA_TEST_SET_ID not set)")

    print("Pre-flight passed.")
    return 0


def run(results_path=None):
    """Main execution: parse results, match TCs, create test runs, upload evidence."""
    url = _get_env('SPIRA_URL')
    username = _get_env('SPIRA_USERNAME')
    api_key = _get_env('SPIRA_API_KEY')
    project_id = int(_get_env('SPIRA_PROJECT_ID'))
    release_id = int(_get_env('SPIRA_RELEASE_ID'))
    test_set_id_str = _get_env('SPIRA_TEST_SET_ID', required=False)
    test_set_id = int(test_set_id_str) if test_set_id_str else None
    auto_create_tc = _get_env('SPIRA_AUTO_CREATE_TEST_CASES', required=False) or 'true'
    auto_create_tc = auto_create_tc.lower() in ('true', '1', 'yes')
    automation_field = _get_env('SPIRA_AUTOMATION_ID_FIELD', required=False) or None

    # Resolve and discover results
    scan_path = _resolve_results_path(results_path)
    logger.info(f"Scanning for results in: {scan_path}")

    results_file, result_type = _discover_results(scan_path)
    if not results_file:
        logger.error(f"No parseable test results found in: {scan_path}")
        return 1

    logger.info(f"Found {result_type} results: {results_file}")

    # Parse
    factory = ParserFactory()
    parser = factory.get_parser(result_type)
    test_results = parser.parse(results_file)
    logger.info(f"Parsed {len(test_results)} test results")

    if not test_results:
        logger.warning("No test results to process")
        return 0

    # Connect to Spira
    client = SpiraAPIClient(url, username, api_key)
    client.authenticate()
    client.validate_release(project_id, release_id)

    # Load test set mappings if test set is configured
    ts_mappings = {}
    if test_set_id:
        client.create_or_get_test_set(project_id, test_set_id, release_id=release_id)
        ts_mappings = client.get_test_set_tc_mappings(project_id, test_set_id)

    # Process each result
    mapper = TestCaseMapper()
    summary = ExecutionSummary(total_tests=len(test_results))
    start = datetime.now()

    for result in test_results:
        tc_id = None

        # TC matching
        if automation_field and result.raw_data:
            auto_id = mapper.extract_automation_id(result.raw_data)
            if auto_id:
                tc_id = client.search_test_case_by_custom_property(
                    project_id, automation_field, auto_id
                )
                if not tc_id and auto_create_tc:
                    tc_id = client.create_test_case_with_custom_property(
                        project_id, result.name, automation_field, auto_id
                    )
                    logger.info(f"Created TC:{tc_id} for {auto_id}")
        else:
            # Fallback: regex TC ID from name
            tc_id_num = mapper.extract_test_case_id(result.raw_data) if result.raw_data else None
            if not tc_id_num:
                tc_id_num = mapper.get_test_case_id(result.name)
            tc_id = tc_id_num

        if not tc_id:
            logger.warning(f"No TC match for: {result.name}")
            summary.skipped_tests += 1
            continue

        # Create test run
        try:
            tstc_id = ts_mappings.get(tc_id) if test_set_id else None

            if test_set_id and not tstc_id:
                logger.warning(
                    f"⚠ TC:{tc_id} is not in Test Set {test_set_id}. "
                    f"Run created but not linked to test set. "
                    f"Add it: {url}/{project_id}/TestSet/{test_set_id}.aspx"
                )

            run_id = client.create_test_run(
                project_id, tc_id, result,
                test_set_id=test_set_id if tstc_id else None,
                test_set_test_case_id=tstc_id
            )
            summary.successful_uploads += 1
            status = "✓" if result.status.name == "PASSED" else "✗"
            logger.info(f"{status} TC:{tc_id} → Run #{run_id} [{result.status.name}]")

            # Upload evidence
            for evidence_path in result.evidence_files:
                try:
                    client.upload_evidence(project_id, run_id, evidence_path)
                    summary.evidence_uploaded += 1
                except Exception as e:
                    logger.warning(f"Evidence upload failed for {evidence_path}: {e}")

        except APIError as e:
            summary.failed_uploads += 1
            logger.error(f"TC:{tc_id} failed: {e}")

    summary.execution_duration = (datetime.now() - start).total_seconds()

    # Summary
    print(f"\n{'='*60}")
    print(f"Total: {summary.total_tests}  Sent: {summary.successful_uploads}  "
          f"Failed: {summary.failed_uploads}  Skipped: {summary.skipped_tests}  "
          f"Evidence: {summary.evidence_uploaded}  Time: {summary.execution_duration:.1f}s")
    print(f"{'='*60}")

    return 1 if summary.failed_uploads > 0 else 0


def main():
    """CLI entry point."""
    setup_logging()
    _load_env_file()

    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print(__doc__)
        print("Environment variables:")
        print("  SPIRA_URL                  Spira instance URL (required)")
        print("  SPIRA_USERNAME             Spira username (required)")
        print("  SPIRA_API_KEY              Spira API key (required)")
        print("  SPIRA_PROJECT_ID           Spira project ID (required)")
        print("  SPIRA_TEST_SET_ID          Spira test set ID (required)")
        print("  SPIRA_RELEASE_ID           Spira release ID (required)")
        print("  SPIRA_RESULTS_DIR          Path to scan for test results")
        print("  SPIRA_RESULT_TYPE          Override format detection")
        print("  SPIRA_AUTOMATION_ID_FIELD  Custom property for TC matching")
        print("  SPIRA_AUTO_CREATE_TEST_CASES  Auto-create TCs (default: true)")
        return 0

    if '--preflight' in args:
        try:
            return run_preflight()
        except Exception as e:
            logger.error(f"Pre-flight failed: {e}")
            return 1

    # Main run — optional positional arg for results path
    results_path = None
    for arg in args:
        if not arg.startswith('-'):
            results_path = arg
            break

    try:
        return run(results_path)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
