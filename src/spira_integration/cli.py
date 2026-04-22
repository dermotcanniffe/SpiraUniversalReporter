"""
spira-report -- CLI entry point for Spira test result integration.

Usage:
    spira-report [results_path]                    # scan path or auto-sense
    spira-report --preflight                       # validate config only
    spira-report --url URL --username USER ...     # pass config as CLI args
    spira-report --help

Config priority: CLI arguments > environment variables > .env file
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


def _inject_system_certs():
    """
    If truststore is installed, use the OS certificate store instead of certifi.
    This makes Python trust the same CAs as the OS (including corporate internal CAs).
    Install with: pip install truststore
    """
    try:
        import truststore
        truststore.inject_into_ssl()
        logging.getLogger(__name__).debug("Using OS certificate store via truststore")
    except ImportError:
        pass  # truststore not installed, use default certifi bundle

# CLI arg name -> env var name mapping
_ARG_TO_ENV = {
    '--url': 'SPIRA_URL',
    '--username': 'SPIRA_USERNAME',
    '--api-key': 'SPIRA_API_KEY',
    '--project-id': 'SPIRA_PROJECT_ID',
    '--release-id': 'SPIRA_RELEASE_ID',
    '--test-set-id': 'SPIRA_TEST_SET_ID',
    '--results-file': 'SPIRA_RESULTS_DIR',
    '--results-dir': 'SPIRA_RESULTS_DIR',
    '--result-type': 'SPIRA_RESULT_TYPE',
    '--automation-id-field': 'SPIRA_AUTOMATION_ID_FIELD',
    '--ssl-verify': 'SPIRA_SSL_VERIFY',
}


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


def _parse_cli_args(args):
    """
    Parse CLI arguments and set them as env vars.
    CLI args override env vars, which override .env file.
    Returns the remaining positional args.
    """
    positional = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in _ARG_TO_ENV and i + 1 < len(args):
            env_key = _ARG_TO_ENV[arg]
            os.environ[env_key] = args[i + 1]
            i += 2
        elif arg.startswith('--') and '=' in arg:
            key, value = arg.split('=', 1)
            if key in _ARG_TO_ENV:
                os.environ[_ARG_TO_ENV[key]] = value
            i += 1
        elif not arg.startswith('-'):
            positional.append(arg)
            i += 1
        else:
            positional.append(arg)
            i += 1
    return positional


def _resolve_results_path(cli_arg=None):
    """Resolve the results path: CLI arg > SPIRA_RESULTS_DIR > cwd."""
    if cli_arg:
        return cli_arg
    env_path = os.environ.get('SPIRA_RESULTS_DIR') or os.environ.get('SPIRA_RESULTS_FILE')
    if env_path:
        return env_path
    return '.'


def _discover_results(scan_path):
    """Auto-sense: scan a directory for parseable test results."""
    factory = ParserFactory()
    path = Path(scan_path)

    if not path.exists():
        logger.error(f"Results path does not exist: {scan_path}")
        return None, None

    if path.is_file():
        try:
            fmt = factory.detect_result_type(str(path))
            return str(path), fmt
        except Exception:
            return None, None

    try:
        fmt = factory.detect_result_type(str(path))
        return str(path), fmt
    except Exception:
        pass

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
        return candidates[0]

    return None, None


def _get_env(name, required=True):
    """Get env var, fail with clear message if required and missing."""
    val = os.environ.get(name, '')
    if required and not val:
        logger.error(f"{name} is not set. Provide via --{name.lower().replace('spira_', '').replace('_', '-')} or set {name} as an environment variable.")
        sys.exit(1)
    return val


def _get_ssl_verify():
    """
    Determine SSL verification setting.
    
    Returns:
        True (default, system CA), False (disabled), or str (path to CA bundle)
    """
    val = os.environ.get('SPIRA_SSL_VERIFY', 'true').strip()
    
    # Boolean values
    if val.lower() in ('true', '1', 'yes', ''):
        return True
    if val.lower() in ('false', '0', 'no'):
        logger.warning("SSL verification disabled (SPIRA_SSL_VERIFY=false)")
        return False
    
    # Treat as path to CA certificate bundle
    if os.path.isfile(val):
        logger.info(f"Using custom CA bundle: {val}")
        return val
    else:
        logger.error(f"SPIRA_SSL_VERIFY points to non-existent file: {val}")
        logger.error("Set to 'true' (system CAs), 'false' (disable), or a path to a CA bundle .pem file")
        sys.exit(1)


def run_preflight():
    """Validate config and connectivity without sending results."""
    print("Pre-flight validation...")
    url = _get_env('SPIRA_URL')
    username = _get_env('SPIRA_USERNAME')
    api_key = _get_env('SPIRA_API_KEY')
    project_id = int(_get_env('SPIRA_PROJECT_ID'))
    release_id = int(_get_env('SPIRA_RELEASE_ID'))
    test_set_id_str = _get_env('SPIRA_TEST_SET_ID', required=False)
    ssl_verify = _get_ssl_verify()

    client = SpiraAPIClient(url, username, api_key, ssl_verify=ssl_verify)

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
    ssl_verify = _get_ssl_verify()

    scan_path = _resolve_results_path(results_path)
    logger.info(f"Scanning for results in: {scan_path}")

    results_file, result_type = _discover_results(scan_path)
    if not results_file:
        logger.error(f"No parseable test results found in: {scan_path}")
        return 1

    logger.info(f"Found {result_type} results: {results_file}")

    factory = ParserFactory()
    parser = factory.get_parser(result_type)
    test_results = parser.parse(results_file)
    logger.info(f"Parsed {len(test_results)} test results")

    if not test_results:
        logger.warning("No test results to process")
        return 0

    client = SpiraAPIClient(url, username, api_key, ssl_verify=ssl_verify)
    client.authenticate()
    client.validate_release(project_id, release_id)

    ts_mappings = {}
    if test_set_id:
        client.create_or_get_test_set(project_id, test_set_id, release_id=release_id)
        ts_mappings = client.get_test_set_tc_mappings(project_id, test_set_id)

    mapper = TestCaseMapper()
    summary = ExecutionSummary(total_tests=len(test_results))
    start = datetime.now()

    for result in test_results:
        tc_id = None

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
            tc_id_num = mapper.extract_test_case_id(result.raw_data) if result.raw_data else None
            if not tc_id_num:
                tc_id_num = mapper.get_test_case_id(result.name)
            tc_id = tc_id_num

        if not tc_id:
            logger.warning(f"No TC match for: {result.name}")
            summary.skipped_tests += 1
            continue

        try:
            tstc_id = ts_mappings.get(tc_id) if test_set_id else None

            if test_set_id and not tstc_id:
                logger.warning(
                    f"TC:{tc_id} is not in Test Set {test_set_id}. "
                    f"Run created but not linked. "
                    f"Add it: {url}/{project_id}/TestSet/{test_set_id}.aspx"
                )

            run_id = client.create_test_run(
                project_id, tc_id, result,
                test_set_id=test_set_id if tstc_id else None,
                test_set_test_case_id=tstc_id
            )
            summary.successful_uploads += 1
            status = "✓" if result.status.name == "PASSED" else "✗"
            logger.info(f"{status} TC:{tc_id} -> Run #{run_id} [{result.status.name}]")

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

    print(f"\n{'='*60}")
    print(f"Total: {summary.total_tests}  Sent: {summary.successful_uploads}  "
          f"Failed: {summary.failed_uploads}  Skipped: {summary.skipped_tests}  "
          f"Evidence: {summary.evidence_uploaded}  Time: {summary.execution_duration:.1f}s")
    print(f"{'='*60}")

    return 1 if summary.failed_uploads > 0 else 0


def main():
    """CLI entry point."""
    setup_logging()
    _inject_system_certs()
    _load_env_file()

    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print(__doc__)
        print("CLI arguments (override env vars):")
        print("  --url URL                  Spira instance URL")
        print("  --username USER            Spira username")
        print("  --api-key KEY              Spira API key")
        print("  --project-id ID            Spira project ID")
        print("  --release-id ID            Spira release ID")
        print("  --test-set-id ID           Spira test set ID (optional)")
        print("  --results-file PATH        Path to test results file or directory")
        print("  --results-dir PATH         Path to test results directory")
        print("  --result-type TYPE         Override format detection")
        print("  --automation-id-field FIELD Custom property for TC matching")
        print("  --ssl-verify true|false    SSL certificate verification (default: true)")
        print()
        print("Environment variables:")
        print("  SPIRA_URL, SPIRA_USERNAME, SPIRA_API_KEY, SPIRA_PROJECT_ID,")
        print("  SPIRA_RELEASE_ID, SPIRA_TEST_SET_ID, SPIRA_RESULTS_DIR,")
        print("  SPIRA_RESULT_TYPE, SPIRA_AUTOMATION_ID_FIELD, SPIRA_SSL_VERIFY,")
        print("  SPIRA_AUTO_CREATE_TEST_CASES")
        print()
        print("Config priority: CLI args > env vars > .env file")
        return 0

    # Parse CLI args into env vars (CLI overrides env)
    remaining = _parse_cli_args(args)

    if '--preflight' in remaining:
        try:
            return run_preflight()
        except Exception as e:
            logger.error(f"Pre-flight failed: {e}")
            return 1

    # Positional arg for results path
    results_path = None
    for arg in remaining:
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
