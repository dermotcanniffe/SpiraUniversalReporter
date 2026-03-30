"""Step definitions for JUnit XML parser feature."""

import tempfile
from pathlib import Path
from behave import given, when, then
from src.spira_integration.parsers.junit_parser import JUnitParser
from src.spira_integration.models import TestStatus
from src.spira_integration.exceptions import ParseError


@given('I have a JUnit parser')
def step_have_junit_parser(context):
    context.parser = JUnitParser()


@given('I have a valid JUnit XML file with single testsuite:')
@given('I have a valid JUnit XML file with single testsuite')
def step_have_junit_xml_single(context):
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write(context.text)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('test result {index:d} should have name "{name}"')
def step_verify_result_name_by_index(context, index, name):
    assert index < len(context.results), f"No result at index {index}"
    actual = context.results[index].name
    # JUnit parser may prepend classname, so check contains
    assert name in actual, f"Expected '{name}' in '{actual}'"


@then('test result {index:d} should have status "{status}"')
def step_verify_result_status_by_index(context, index, status):
    assert index < len(context.results), f"No result at index {index}"
    expected = TestStatus[status]
    assert context.results[index].status == expected, \
        f"Expected {expected}, got {context.results[index].status}"


@then('test result {index:d} should have error message "{message}"')
def step_verify_result_error_by_index(context, index, message):
    assert index < len(context.results), f"No result at index {index}"
    actual = context.results[index].error_message or ''
    assert message in actual, f"Expected '{message}' in error, got '{actual}'"


@given('I have a JUnit XML file with multiple testsuites')
def step_have_junit_multiple_suites(context):
    xml = """<?xml version="1.0"?>
    <testsuites>
      <testsuite name="Suite1" tests="1"><testcase name="t1" classname="S1"/></testsuite>
      <testsuite name="Suite2" tests="1"><testcase name="t2" classname="S2"/></testsuite>
    </testsuites>"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write(xml)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('I should get test results from all testsuites')
def step_verify_results_from_all_suites(context):
    assert len(context.results) >= 2, f"Expected results from multiple suites, got {len(context.results)}"


@given('I have a JUnit XML testcase with time="{time}"')
def step_have_junit_with_time(context, time):
    xml = f"""<?xml version="1.0"?>
    <testsuite name="Suite" tests="1">
      <testcase name="timed_test" classname="Tests" time="{time}"/>
    </testsuite>"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write(xml)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('the test result should have duration {duration} seconds')
def step_verify_duration_seconds(context, duration):
    assert len(context.results) > 0
    expected = float(duration)
    actual = context.results[0].duration
    assert actual is not None, "Duration is None"
    assert abs(actual - expected) < 0.01, f"Expected {expected}s, got {actual}s"


@given('I have a JUnit XML testcase with <skipped/> element')
def step_have_junit_skipped(context):
    xml = """<?xml version="1.0"?>
    <testsuite name="Suite" tests="1">
      <testcase name="skipped_test" classname="Tests"><skipped/></testcase>
    </testsuite>"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write(xml)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@given('I have a JUnit XML testcase with <error> element')
def step_have_junit_error(context):
    xml = """<?xml version="1.0"?>
    <testsuite name="Suite" tests="1">
      <testcase name="error_test" classname="Tests">
        <error message="NullPointerException">java.lang.NullPointerException at Test.java:10</error>
      </testcase>
    </testsuite>"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write(xml)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('the test result should have the error message from the element')
def step_verify_error_from_element(context):
    assert len(context.results) > 0
    result = context.results[0]
    assert result.error_message is not None, "Error message is None"
    assert result.status == TestStatus.FAILED


@given('I have a JUnit XML with system-out containing "EVIDENCE: {path}"')
def step_have_junit_with_evidence(context, path):
    xml = f"""<?xml version="1.0"?>
    <testsuite name="Suite" tests="1">
      <testcase name="evidence_test" classname="Tests">
        <system-out>EVIDENCE: {path}</system-out>
      </testcase>
    </testsuite>"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write(xml)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('the test result should have evidence file "{path}"')
def step_verify_evidence_file_path(context, path):
    assert len(context.results) > 0
    evidence = context.results[0].evidence_files
    # Normalize paths for cross-platform comparison
    normalized = [f.replace('\\', '/') for f in evidence]
    assert any(path.replace('\\', '/') in f for f in normalized), \
        f"Expected '{path}' in evidence, got {evidence}"


@given('I have an invalid XML file')
def step_have_invalid_xml(context):
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write('<<< not valid xml >>>')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@given('I have a TestNG-generated JUnit XML file')
def step_have_testng_xml(context):
    xml = """<?xml version="1.0"?>
    <testsuite name="TestNG Suite" tests="2" failures="0" time="2.0" timestamp="2026-03-26T18:55:58">
      <testcase name="testLogin" classname="com.example.LoginTest" time="1.0"/>
      <testcase name="testLogout" classname="com.example.LoginTest" time="1.0"/>
    </testsuite>"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write(xml)
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('the test results should be extracted correctly')
def step_verify_results_extracted(context):
    assert len(context.results) >= 2, f"Expected at least 2 results, got {len(context.results)}"
    for r in context.results:
        assert r.name is not None
        assert r.status is not None
