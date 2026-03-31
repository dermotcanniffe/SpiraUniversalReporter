"""Step definitions for ExtentReports HTML parser feature."""

import os
import tempfile
import shutil
from pathlib import Path
from behave import given, when, then
from src.spira_integration.parsers.extent_parser import ExtentParser
from src.spira_integration.models import TestStatus
from src.spira_integration.exceptions import ParseError


SUMMARY_TEMPLATE = """<!DOCTYPE html><html><head>
<title>Test Automation Summary Report</title>
</head><body class='extent dark'>
<ul id='test-collection' class='test-collection'>
<li class='test displayed active has-leaf {status}' status='{status}'>
<ul class='collapsible node-list'>{nodes}</ul>
</li></ul></body></html>"""

NODE_TEMPLATE = """<li class='node level-1 leaf {status}' status='{status}'>
<div class='collapsible-header'>
<div class='node-name'>{name}</div>
<span class='node-time'>{time}</span>
<span class='node-duration'>{duration}</span>
</div>
<div class='collapsible-body'><div class='node-steps'>
<table class='bordered table-results'><tbody>{steps}</tbody></table>
</div></div></li>"""

STEP_ROW = """<tr class='log' status='{status}'>
<td class='status {status}'></td><td class='timestamp'>{time}</td>
<td class='step-details'>{details}</td></tr>"""


def _make_summary_dir(context, nodes_html, test_name=None):
    """Create a temp directory with Summary.html and optional test subdirs."""
    temp_dir = tempfile.mkdtemp()
    with open(os.path.join(temp_dir, 'Summary.html'), 'w') as f:
        f.write(SUMMARY_TEMPLATE.format(status='fail', nodes=nodes_html))
    context.temp_files.append(temp_dir)
    context.test_file = temp_dir
    context.test_dir = temp_dir
    return temp_dir


@given('I have an ExtentReports parser')
def step_have_extent_parser(context):
    context.parser = ExtentParser()


@given('I have a directory containing Summary.html with {count:d} test cases')
def step_have_extent_dir_with_n_tests(context, count):
    nodes = ''
    for i in range(count):
        name = f'Test_{i+1}'
        step = STEP_ROW.format(status='pass', time='6:55:58 PM', details='Step passed')
        nodes += NODE_TEMPLATE.format(
            name=name, status='pass', time='Mar 26, 2026 06:55:58 PM',
            duration='0h 0m 1s+0ms', steps=step
        )
    _make_summary_dir(context, nodes)


@when('I parse the directory')
def step_parse_directory(context):
    try:
        context.results = context.parser.parse(context.test_file)
        context.error = None
    except ParseError as e:
        context.error = e
        context.results = []


@given('I have a Summary.html with test "{name}"')
def step_have_summary_with_test(context, name):
    step = STEP_ROW.format(status='pass', time='6:55:58 PM', details='OK')
    node = NODE_TEMPLATE.format(
        name=name, status='pass', time='Mar 26, 2026 06:55:58 PM',
        duration='0h 0m 1s+0ms', steps=step
    )
    _make_summary_dir(context, node)


@when('I parse results with the following statuses:')
def step_parse_extent_statuses(context):
    context.status_mappings = []
    for row in context.table:
        status = row['extent_status']
        expected = row['expected_status']
        step = STEP_ROW.format(status=status, time='6:55:58 PM', details='test')
        node = NODE_TEMPLATE.format(
            name=f'Test_{status}', status=status,
            time='Mar 26, 2026 06:55:58 PM', duration='0h 0m 1s+0ms', steps=step
        )
        temp_dir = tempfile.mkdtemp()
        with open(os.path.join(temp_dir, 'Summary.html'), 'w') as f:
            f.write(SUMMARY_TEMPLATE.format(status=status, nodes=node))
        context.temp_files.append(temp_dir)
        results = context.parser.parse(temp_dir)
        context.status_mappings.append({
            'extent': status, 'expected': expected,
            'actual': results[0].status.name if results else None
        })


@given('I have a test node with time "{time}" and duration "{duration}"')
def step_have_node_with_time(context, time, duration):
    step = STEP_ROW.format(status='pass', time='6:55:58 PM', details='OK')
    node = NODE_TEMPLATE.format(
        name='TimedTest', status='pass', time=time, duration=duration, steps=step
    )
    _make_summary_dir(context, node)


@then('the test result should have a valid start timestamp')
def step_verify_valid_timestamp(context):
    assert len(context.results) > 0
    assert context.results[0].start_time is not None, "Start time is None"


@then('the test result should have duration approximately {expected} seconds')
def step_verify_approx_duration(context, expected):
    assert len(context.results) > 0
    actual = context.results[0].duration
    assert actual is not None, "Duration is None"
    assert abs(actual - float(expected)) < 1.0, f"Expected ~{expected}s, got {actual}s"


@given('I have a test node with failed steps containing error details')
def step_have_node_with_errors(context):
    step = STEP_ROW.format(
        status='fail', time='6:56:12 PM',
        details='Element Validation - Element not found: net::ERR_NAME_NOT_RESOLVED'
    )
    node = NODE_TEMPLATE.format(
        name='FailedTest', status='fail',
        time='Mar 26, 2026 06:55:58 PM', duration='0h 0m 10s+0ms', steps=step
    )
    _make_summary_dir(context, node)


@then('the test result should have an error message')
def step_verify_has_error_message(context):
    assert len(context.results) > 0
    assert context.results[0].error_message is not None, "Error message is None"
    assert len(context.results[0].error_message) > 0


@given('I have a test "{name}" with a Screenshots directory containing {count:d} PNG files')
def step_have_test_with_screenshots(context, name, count):
    step = STEP_ROW.format(status='fail', time='6:55:58 PM', details='Failed')
    node = NODE_TEMPLATE.format(
        name=name, status='fail', time='Mar 26, 2026 06:55:58 PM',
        duration='0h 0m 10s+0ms', steps=step
    )
    temp_dir = _make_summary_dir(context, node)
    # Create test subdirectory with screenshots
    tc_dir = os.path.join(temp_dir, f'{name}_26-Mar-26 06-55-56-870')
    ss_dir = os.path.join(tc_dir, 'Screenshots')
    os.makedirs(ss_dir)
    for i in range(count):
        with open(os.path.join(ss_dir, f'{i+1}_Step{i+1}.png'), 'wb') as f:
            f.write(b'\x89PNG')  # minimal PNG header


@then('each evidence file should be a PNG path')
def step_verify_all_png(context):
    assert len(context.results) > 0
    for f in context.results[0].evidence_files:
        assert f.endswith('.png'), f"Expected PNG, got {f}"


@given('I have a test "{name}" with a ConsolidatedScreenshots directory containing a DOCX file')
def step_have_test_with_consolidated(context, name):
    step = STEP_ROW.format(status='fail', time='6:55:58 PM', details='Failed')
    node = NODE_TEMPLATE.format(
        name=name, status='fail', time='Mar 26, 2026 06:55:58 PM',
        duration='0h 0m 10s+0ms', steps=step
    )
    temp_dir = _make_summary_dir(context, node)
    tc_dir = os.path.join(temp_dir, f'{name}_26-Mar-26 06-55-56-870')
    cs_dir = os.path.join(tc_dir, 'ConsolidatedScreenshots')
    os.makedirs(cs_dir)
    with open(os.path.join(cs_dir, 'Consolidated Screenshots.docx'), 'wb') as f:
        f.write(b'PK')  # minimal docx header


@then('the evidence files should include the DOCX file')
def step_verify_docx_in_evidence(context):
    assert len(context.results) > 0
    evidence = context.results[0].evidence_files
    assert any(f.endswith('.docx') for f in evidence), f"No DOCX in evidence: {evidence}"


@given('Summary.html is nested 2 directories deep')
def step_summary_nested_deep(context):
    temp_dir = tempfile.mkdtemp()
    nested = os.path.join(temp_dir, 'Result', 'Report_timestamp')
    os.makedirs(nested)
    step = STEP_ROW.format(status='pass', time='6:55:58 PM', details='OK')
    node = NODE_TEMPLATE.format(
        name='NestedTest', status='pass', time='Mar 26, 2026 06:55:58 PM',
        duration='0h 0m 1s+0ms', steps=step
    )
    with open(os.path.join(nested, 'Summary.html'), 'w') as f:
        f.write(SUMMARY_TEMPLATE.format(status='pass', nodes=node))
    context.temp_files.append(temp_dir)
    context.test_file = temp_dir


@when('I parse the top-level directory')
def step_parse_top_level(context):
    try:
        context.results = context.parser.parse(context.test_file)
        context.error = None
    except ParseError as e:
        context.error = e
        context.results = []


@then('the parser should find and parse Summary.html')
def step_verify_found_summary(context):
    assert context.error is None, f"Parser error: {context.error}"
    assert len(context.results) > 0, "No results parsed"


@given('I have an empty directory')
def step_have_empty_dir(context):
    temp_dir = tempfile.mkdtemp()
    context.temp_files.append(temp_dir)
    context.test_file = temp_dir


@when('I attempt to parse the directory')
def step_attempt_parse_dir(context):
    try:
        context.results = context.parser.parse(context.test_file)
        context.error = None
    except ParseError as e:
        context.error = e
        context.results = []


@then('the error message should indicate Summary.html was not found')
def step_verify_summary_not_found_error(context):
    assert context.error is not None, "Expected ParseError"
    assert 'summary' in str(context.error).lower() or 'not found' in str(context.error).lower(), \
        f"Expected Summary.html not found error, got: {context.error}"
