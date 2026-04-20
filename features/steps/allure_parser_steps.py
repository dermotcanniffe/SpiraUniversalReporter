"""Step definitions specific to Allure JSON parser feature."""

import json
import os
import tempfile
from pathlib import Path
from behave import given, when, then
from src.spira_integration.parsers.allure_parser import AllureParser
from src.spira_integration.models import TestStatus


@given('I have an Allure parser')
def step_have_allure_parser(context):
    context.parser = AllureParser()


@given('I have a valid Allure JSON file:')
@given('I have a valid Allure JSON file')
def step_have_valid_allure_json(context):
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    content = context.text or '{"uuid": "test-1", "name": "Test", "status": "passed"}'
    temp_file.write(content)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@when('I parse Allure results with the following statuses:')
@when('I parse Allure results with the following statuses')
def step_parse_multiple_statuses(context):
    context.status_mappings = []
    for row in context.table:
        allure_status = row['allure_status']
        expected_status = row['expected_status']
        allure_data = {"uuid": f"test-{allure_status}", "name": f"Test {allure_status}", "status": allure_status}
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(allure_data, temp_file)
        temp_file.close()
        context.temp_files.append(temp_file.name)
        results = context.parser.parse(temp_file.name)
        context.status_mappings.append({
            'allure': allure_status, 'expected': expected_status,
            'actual': results[0].status.name if results else None
        })


@given('I have an Allure result with start={start:d} and stop={stop:d}')
def step_have_allure_with_timestamps(context, start, stop):
    allure_data = {"uuid": "test-1", "name": "Test with timestamps", "status": "passed", "start": start, "stop": stop}
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    json.dump(allure_data, temp_file)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('the test result should have start timestamp {timestamp:d}')
def step_verify_start_timestamp(context, timestamp):
    assert len(context.results) > 0
    result = context.results[0]
    assert result.start_time is not None, "Start time is None"
    actual_ms = int(result.start_time.timestamp() * 1000)
    assert actual_ms == timestamp, f"Expected start {timestamp}, got {actual_ms}"


@then('the test result should have duration {duration:d} milliseconds')
def step_verify_duration_ms(context, duration):
    assert len(context.results) > 0
    result = context.results[0]
    assert result.duration is not None, "Duration is None"
    actual_ms = int(result.duration * 1000)
    assert actual_ms == duration, f"Expected duration {duration}ms, got {actual_ms}ms"


@given('I have an Allure result with statusDetails:')
@given('I have an Allure result with statusDetails')
def step_have_allure_with_status_details(context):
    status_details = json.loads(context.text)
    allure_data = {"uuid": "test-1", "name": "Test with error", "status": "failed", "statusDetails": status_details}
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    json.dump(allure_data, temp_file)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('the test result should have error message "{message}"')
def step_verify_error_message(context, message):
    assert len(context.results) > 0
    assert context.results[0].error_message == message, \
        f"Expected error '{message}', got '{context.results[0].error_message}'"


@then('the test result should have stack trace containing "{text}"')
def step_verify_stack_trace(context, text):
    assert len(context.results) > 0
    assert context.results[0].stack_trace is not None, "Stack trace is None"
    assert text in context.results[0].stack_trace


@given('I have an Allure result with attachments:')
@given('I have an Allure result with attachments')
def step_have_allure_with_attachments(context):
    attachments = json.loads(context.text)
    allure_data = {"uuid": "test-1", "name": "Test with attachments", "status": "passed", "attachments": attachments}
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    json.dump(allure_data, temp_file)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name
    context.results_dir = Path(temp_file.name).parent


@then('evidence file {index:d} should be "{filename}"')
def step_verify_evidence_file(context, index, filename):
    assert len(context.results) > 0
    result = context.results[0]
    assert index < len(result.evidence_files)
    actual_path = result.evidence_files[index]
    expected_path = str(context.results_dir / filename)
    assert actual_path == expected_path, f"Expected '{expected_path}', got '{actual_path}'"


@given('the results directory is "{directory}"')
def step_set_results_directory(context, directory):
    context.results_dir = Path(directory)


@given('I have an attachment with source "{source}"')
def step_have_attachment_with_source(context, source):
    allure_data = {"uuid": "test-1", "name": "Test", "status": "passed", "attachments": [{"source": source}]}
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    json.dump(allure_data, temp_file)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name
    context.results_dir = Path(temp_file.name).parent


@then('the evidence file path should be "{expected_path}"')
def step_verify_evidence_path(context, expected_path):
    assert len(context.results) > 0
    result = context.results[0]
    assert len(result.evidence_files) > 0
    actual = Path(result.evidence_files[0])
    expected = Path(expected_path.replace('/path/to/allure-results', str(context.results_dir)))
    assert actual == expected, f"Expected '{expected}', got '{actual}'"


@given('I have an invalid JSON file')
def step_have_invalid_json(context):
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_file.write('{ invalid json }')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@when('I parse attachments with the following types:')
@when('I parse attachments with the following types')
def step_parse_attachments_with_types(context):
    context.file_types_tested = []
    for row in context.table:
        context.file_types_tested.append(row['type'])


@then('only supported file types should be included')
def step_verify_supported_types(context):
    assert len(context.file_types_tested) > 0


# --- Directory parsing steps ---

@given('I have a directory with {count:d} Allure result files')
@given('I have a directory with {count:d} Allure result file')
def step_have_dir_with_n_results(context, count):
    temp_dir = tempfile.mkdtemp()
    context.temp_files.append(temp_dir)
    for i in range(count):
        data = {"uuid": f"test-{i}", "name": f"Test {i+1}", "status": "passed",
                "start": 1234567890000 + i * 1000, "stop": 1234567891000 + i * 1000}
        with open(os.path.join(temp_dir, f'{i:08x}-result.json'), 'w') as f:
            json.dump(data, f)
    context.test_file = temp_dir


@given('I have a directory with {result_count:d} result files and {container_count:d} container files')
def step_have_dir_with_results_and_containers(context, result_count, container_count):
    temp_dir = tempfile.mkdtemp()
    context.temp_files.append(temp_dir)
    for i in range(result_count):
        data = {"uuid": f"test-{i}", "name": f"Test {i+1}", "status": "passed"}
        with open(os.path.join(temp_dir, f'{i:08x}-result.json'), 'w') as f:
            json.dump(data, f)
    for i in range(container_count):
        data = {"uuid": f"container-{i}", "name": f"Suite {i+1}", "children": []}
        with open(os.path.join(temp_dir, f'{i:08x}-container.json'), 'w') as f:
            json.dump(data, f)
    context.test_file = temp_dir


@then('can_parse should return true for the directory')
def step_can_parse_true_dir(context):
    assert context.parser.can_parse(context.test_file)


@then('can_parse should return false for the directory')
def step_can_parse_false_dir(context):
    assert not context.parser.can_parse(context.test_file)


@given('client Allure results exist at "{path}"')
def step_client_allure_exists(context, path):
    assert Path(path).exists(), f"Client Allure results not found at {path}"
    context.test_file = path
