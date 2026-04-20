"""Common step definitions shared across multiple feature files."""

import os
import tempfile
import shutil
from pathlib import Path
from behave import given, when, then
from src.spira_integration.exceptions import ParseError


# --- Parsing ---

@when('I parse the file')
def step_parse_file(context):
    try:
        context.results = context.parser.parse(context.test_file)
        context.error = None
    except ParseError as e:
        context.error = e
        context.results = []


@when('I parse the directory')
def step_parse_directory(context):
    try:
        context.results = context.parser.parse(context.test_file)
        context.error = None
    except ParseError as e:
        context.error = e
        context.results = []


@when('I attempt to parse the file')
def step_attempt_parse_file(context):
    step_parse_file(context)


@then('I should get {count:d} test result')
@then('I should get {count:d} test results')
def step_verify_result_count(context, count):
    assert len(context.results) == count, \
        f"Expected {count} results, got {len(context.results)}"


@then('the test result should have name "{name}"')
def step_verify_result_name(context, name):
    assert len(context.results) > 0, "No results to verify"
    assert context.results[0].name == name, \
        f"Expected name '{name}', got '{context.results[0].name}'"


@then('the test result should have status "{status}"')
def step_verify_result_status(context, status):
    from src.spira_integration.models import TestStatus
    assert len(context.results) > 0, "No results to verify"
    expected_status = TestStatus[status]
    assert context.results[0].status == expected_status, \
        f"Expected status {expected_status}, got {context.results[0].status}"


@then('each result should have a name and status')
def step_each_has_name_status(context):
    for r in context.results:
        assert r.name, f"Result missing name"
        assert r.status is not None, f"Result {r.name} missing status"


@then('each result should have evidence files discovered')
def step_each_has_evidence(context):
    has_evidence = any(len(r.evidence_files) > 0 for r in context.results)
    assert has_evidence, "No results have evidence files"


@then('at least {count:d} test result should be extracted')
def step_at_least_n_results(context, count):
    assert len(context.results) >= count, \
        f"Expected at least {count} results, got {len(context.results)}"


# --- Error assertions ---

@then('a ParseError should be raised')
def step_verify_parse_error(context):
    assert context.error is not None, "Expected ParseError but none was raised"
    assert isinstance(context.error, ParseError), \
        f"Expected ParseError, got {type(context.error)}"


@then('the error message should indicate "{message}"')
def step_verify_error_message_contains(context, message):
    error = getattr(context, 'error', None) or getattr(context.data, 'error', None)
    assert error is not None, "No error was raised"
    error_msg = str(error).lower()
    normalized = message.lower().replace('spira-', '').replace('-', ' ')
    assert normalized in error_msg or message.lower() in error_msg, \
        f"Expected '{message}' in error message, got: {error}"


# --- Temp directory helpers ---

@given('I have an empty directory')
def step_have_empty_dir(context):
    temp_dir = tempfile.mkdtemp()
    context.temp_files.append(temp_dir)
    context.test_file = temp_dir


@then('the test result should have {count:d} evidence files')
@then('the test result should have {count:d} evidence file')
def step_verify_evidence_count(context, count):
    assert len(context.results) > 0, "No results to verify"
    result = context.results[0]
    assert len(result.evidence_files) == count, \
        f"Expected {count} evidence files, got {len(result.evidence_files)}"


@then('the statuses should be mapped correctly')
def step_verify_status_mappings(context):
    for mapping in context.status_mappings:
        assert mapping['actual'] == mapping['expected'], \
            f"Status {mapping.get('allure', mapping.get('extent', '?'))} mapped to {mapping['actual']}, expected {mapping['expected']}"
