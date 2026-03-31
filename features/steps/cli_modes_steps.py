"""Step definitions for CLI operational modes feature."""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from behave import given, when, then


@when('I run spira-report with --help')
def step_run_help(context):
    from src.spira_integration.cli import main
    old_argv = sys.argv
    sys.argv = ['spira-report', '--help']
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        context.exit_code = main()
    finally:
        context.cli_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        sys.argv = old_argv


@when('I run spira-report with --preflight')
def step_run_preflight(context):
    from src.spira_integration.cli import main
    old_argv = sys.argv
    sys.argv = ['spira-report', '--preflight']
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        context.exit_code = main()
    finally:
        context.cli_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        sys.argv = old_argv


@then('the output should include "{text}"')
def step_output_includes(context, text):
    assert text in context.cli_output, \
        f"Expected '{text}' in output, got:\n{context.cli_output[:500]}"


@then('the exit code should be {code:d}')
def step_exit_code(context, code):
    assert context.exit_code == code, \
        f"Expected exit code {code}, got {context.exit_code}"


# --- Auto-sense discovery ---

@given('a temporary directory containing a valid Allure JSON file')
def step_temp_dir_allure(context):
    d = tempfile.mkdtemp()
    with open(os.path.join(d, 'result.json'), 'w') as f:
        json.dump({'uuid': 'test-1', 'name': 'Test', 'status': 'passed'}, f)
    context.temp_files.append(d)
    context.scan_dir = d


@given('a temporary directory containing a valid JUnit XML file')
def step_temp_dir_junit(context):
    d = tempfile.mkdtemp()
    with open(os.path.join(d, 'results.xml'), 'w') as f:
        f.write('<?xml version="1.0"?><testsuite name="S"><testcase name="t"/></testsuite>')
    context.temp_files.append(d)
    context.scan_dir = d


@given('a temporary directory containing a Summary.html')
def step_temp_dir_extent(context):
    d = tempfile.mkdtemp()
    with open(os.path.join(d, 'Summary.html'), 'w') as f:
        f.write("""<!DOCTYPE html><html><body class='extent dark'>
        <ul id='test-collection'><li class='test displayed active has-leaf pass' status='pass'>
        <ul class='collapsible node-list'>
        <li class='node level-1 leaf pass' status='pass'>
        <div class='collapsible-header'><div class='node-name'>Test1</div>
        <span class='node-time'>Mar 26, 2026 06:55:58 PM</span>
        <span class='node-duration'>0h 0m 1s+0ms</span></div>
        <div class='collapsible-body'><div class='node-steps'>
        <table class='bordered table-results'><tbody>
        <tr class='log' status='pass'><td class='status pass'></td>
        <td class='timestamp'>6:55:58 PM</td>
        <td class='step-details'>OK</td></tr>
        </tbody></table></div></div></li></ul></li></ul></body></html>""")
    context.temp_files.append(d)
    context.scan_dir = d


@given('an empty temporary directory')
def step_temp_dir_empty(context):
    d = tempfile.mkdtemp()
    context.temp_files.append(d)
    context.scan_dir = d


@when('I run the auto-sense discovery on that directory')
def step_run_discover(context):
    from src.spira_integration.cli import _discover_results
    context.discovered_path, context.discovered_format = _discover_results(context.scan_dir)


@then('the discovered format should be "{fmt}"')
def step_verify_discovered_format(context, fmt):
    assert context.discovered_format == fmt, \
        f"Expected '{fmt}', got '{context.discovered_format}'"


@then('no results should be discovered')
def step_no_results_discovered(context):
    assert context.discovered_path is None and context.discovered_format is None, \
        f"Expected no results, got {context.discovered_format}: {context.discovered_path}"


# --- Results path resolution ---

@given('SPIRA_RESULTS_DIR is set to "{path}"')
def step_set_results_dir(context, path):
    context.original_env['SPIRA_RESULTS_DIR'] = os.environ.get('SPIRA_RESULTS_DIR')
    os.environ['SPIRA_RESULTS_DIR'] = path


@given('SPIRA_RESULTS_DIR is not set')
def step_unset_results_dir(context):
    context.original_env['SPIRA_RESULTS_DIR'] = os.environ.pop('SPIRA_RESULTS_DIR', None)
    context.original_env['SPIRA_RESULTS_FILE'] = os.environ.pop('SPIRA_RESULTS_FILE', None)


@when('I resolve the results path with no CLI argument')
def step_resolve_no_arg(context):
    from src.spira_integration.cli import _resolve_results_path
    context.resolved_path = _resolve_results_path(None)


@when('I resolve the results path with CLI argument "{path}"')
def step_resolve_with_arg(context, path):
    from src.spira_integration.cli import _resolve_results_path
    context.resolved_path = _resolve_results_path(path)


@then('the resolved path should be "{expected}"')
def step_verify_resolved_path(context, expected):
    assert context.resolved_path == expected, \
        f"Expected '{expected}', got '{context.resolved_path}'"
