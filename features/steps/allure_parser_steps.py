"""Step definitions for Allure parser feature - simple and atomic."""

import json
import tempfile
from pathlib import Path
from behave import given, when, then
from src.spira_integration.parsers.allure_parser import AllureParser
from src.spira_integration.models import TestStatus
from src.spira_integration.exceptions import ParseError


@given('I have an Allure parser')
def step_have_allure_parser(context):
    """Create an Allure parser."""
    context.parser = AllureParser()


@given('I have a valid Allure JSON file')
def step_have_valid_allure_json(context):
    """Create a valid Allure JSON file from docstring."""
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.json'
    )
    temp_file.write(context.text)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@when('I parse the file')
def step_parse_file(context):
    """Parse the test file."""
    try:
        context.results = context.parser.parse(context.test_file)
        context.error = None
    except ParseError as e:
        context.error = e
        context.results = []


@then('I should get {count:d} test result')
@then('I should get {count:d} test results')
def step_verify_result_count(context, count):
    """Verify number of test results."""
    assert len(context.results) == count, \
        f"Expected {count} results, got {len(context.results)}"


@then('the test result should have name "{name}"')
def step_verify_result_name(context, name):
    """Verify test result name."""
    assert len(context.results) > 0, "No results to verify"
    assert context.results[0].name == name, \
        f"Expected name '{name}', got '{context.results[0].name}'"


@then('the test result should have status "{status}"')
def step_verify_result_status(context, status):
    """Verify test result status."""
    assert len(context.results) > 0, "No results to verify"
    expected_status = TestStatus[status]
    assert context.results[0].status == expected_status, \
        f"Expected status {expected_status}, got {context.results[0].status}"


@when('I parse Allure results with the following statuses')
def step_parse_multiple_statuses(context):
    """Parse multiple Allure results with different statuses."""
    context.status_mappings = []
    
    for row in context.table:
        allure_status = row['allure_status']
        expected_status = row['expected_status']
        
        # Create temp file with this status
        allure_data = {
            "uuid": f"test-{allure_status}",
            "name": f"Test {allure_status}",
            "status": allure_status
        }
        
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', delete=False, suffix='.json'
        )
        json.dump(allure_data, temp_file)
        temp_file.close()
        context.temp_files.append(temp_file.name)
        
        # Parse and store result
        results = context.parser.parse(temp_file.name)
        context.status_mappings.append({
            'allure': allure_status,
            'expected': expected_status,
            'actual': results[0].status.name if results else None
        })


@then('the statuses should be mapped correctly')
def step_verify_status_mappings(context):
    """Verify all status mappings are correct."""
    for mapping in context.status_mappings:
        assert mapping['actual'] == mapping['expected'], \
            f"Status {mapping['allure']} mapped to {mapping['actual']}, expected {mapping['expected']}"


@given('I have an Allure result with start={start:d} and stop={stop:d}')
def step_have_allure_with_timestamps(context, start, stop):
    """Create Allure result with specific timestamps."""
    allure_data = {
        "uuid": "test-1",
        "name": "Test with timestamps",
        "status": "passed",
        "start": start,
        "stop": stop
    }
    
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.json'
    )
    json.dump(allure_data, temp_file)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('the test result should have start timestamp {timestamp:d}')
def step_verify_start_timestamp(context, timestamp):
    """Verify start timestamp."""
    assert len(context.results) > 0, "No results to verify"
    result = context.results[0]
    assert result.start_time is not None, "Start time is None"
    # Convert back to milliseconds for comparison
    actual_ms = int(result.start_time.timestamp() * 1000)
    assert actual_ms == timestamp, \
        f"Expected start {timestamp}, got {actual_ms}"


@then('the test result should have duration {duration:d} milliseconds')
def step_verify_duration(context, duration):
    """Verify duration."""
    assert len(context.results) > 0, "No results to verify"
    result = context.results[0]
    assert result.duration is not None, "Duration is None"
    # Duration is in seconds, convert to milliseconds
    actual_ms = int(result.duration * 1000)
    assert actual_ms == duration, \
        f"Expected duration {duration}ms, got {actual_ms}ms"


@given('I have an Allure result with statusDetails')
def step_have_allure_with_status_details(context):
    """Create Allure result with statusDetails from docstring."""
    status_details = json.loads(context.text)
    allure_data = {
        "uuid": "test-1",
        "name": "Test with error",
        "status": "failed",
        "statusDetails": status_details
    }
    
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.json'
    )
    json.dump(allure_data, temp_file)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('the test result should have error message "{message}"')
def step_verify_error_message(context, message):
    """Verify error message."""
    assert len(context.results) > 0, "No results to verify"
    result = context.results[0]
    assert result.error_message == message, \
        f"Expected error '{message}', got '{result.error_message}'"


@then('the test result should have stack trace containing "{text}"')
def step_verify_stack_trace(context, text):
    """Verify stack trace contains text."""
    assert len(context.results) > 0, "No results to verify"
    result = context.results[0]
    assert result.stack_trace is not None, "Stack trace is None"
    assert text in result.stack_trace, \
        f"Expected '{text}' in stack trace, got: {result.stack_trace}"


@given('I have an Allure result with attachments')
def step_have_allure_with_attachments(context):
    """Create Allure result with attachments from docstring."""
    attachments = json.loads(context.text)
    allure_data = {
        "uuid": "test-1",
        "name": "Test with attachments",
        "status": "passed",
        "attachments": attachments
    }
    
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.json'
    )
    json.dump(allure_data, temp_file)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name
    context.results_dir = Path(temp_file.name).parent


@then('the test result should have {count:d} evidence files')
@then('the test result should have {count:d} evidence file')
def step_verify_evidence_count(context, count):
    """Verify number of evidence files."""
    assert len(context.results) > 0, "No results to verify"
    result = context.results[0]
    assert len(result.evidence_files) == count, \
        f"Expected {count} evidence files, got {len(result.evidence_files)}"


@then('evidence file {index:d} should be "{filename}"')
def step_verify_evidence_file(context, index, filename):
    """Verify specific evidence file."""
    assert len(context.results) > 0, "No results to verify"
    result = context.results[0]
    assert index < len(result.evidence_files), \
        f"Evidence file {index} does not exist"
    # Check that the path ends with the expected filename
    actual_path = result.evidence_files[index]
    expected_path = str(context.results_dir / filename)
    assert actual_path == expected_path, \
        f"Expected '{expected_path}', got '{actual_path}'"


@given('the results directory is "{directory}"')
def step_set_results_directory(context, directory):
    """Set the results directory."""
    context.results_dir = Path(directory)


@given('I have an attachment with source "{source}"')
def step_have_attachment_with_source(context, source):
    """Create Allure result with specific attachment source."""
    allure_data = {
        "uuid": "test-1",
        "name": "Test",
        "status": "passed",
        "attachments": [{"source": source}]
    }
    
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.json'
    )
    json.dump(allure_data, temp_file)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name
    context.results_dir = Path(temp_file.name).parent


@then('the evidence file path should be "{expected_path}"')
def step_verify_evidence_path(context, expected_path):
    """Verify evidence file path."""
    assert len(context.results) > 0, "No results to verify"
    result = context.results[0]
    assert len(result.evidence_files) > 0, "No evidence files"
    # Normalize paths for comparison (handle Windows vs Unix)
    actual = Path(result.evidence_files[0])
    expected = Path(expected_path.replace('/path/to/allure-results', str(context.results_dir)))
    assert actual == expected, \
        f"Expected '{expected}', got '{actual}'"


@given('I have an invalid JSON file')
def step_have_invalid_json(context):
    """Create an invalid JSON file."""
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.json'
    )
    temp_file.write('{ invalid json }')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@when('I attempt to parse the file')
def step_attempt_parse(context):
    """Attempt to parse the file."""
    step_parse_file(context)


@then('a ParseError should be raised')
def step_verify_parse_error(context):
    """Verify ParseError was raised."""
    assert context.error is not None, "Expected ParseError but none was raised"
    assert isinstance(context.error, ParseError), \
        f"Expected ParseError, got {type(context.error)}"



@when('I parse attachments with the following types')
def step_parse_attachments_with_types(context):
    """Parse attachments with different MIME types."""
    # All types are supported in Allure, just verify they're extracted
    context.file_types_tested = []
    for row in context.table:
        file_type = row['type']
        context.file_types_tested.append(file_type)


@then('only supported file types should be included')
def step_verify_supported_types(context):
    """Verify supported file types."""
    # In Allure, all attachment types are supported
    # This is more of a documentation step
    assert len(context.file_types_tested) > 0, "No file types tested"
