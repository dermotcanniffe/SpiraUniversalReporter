"""Step definitions for test case mapper feature."""

from behave import given, when, then
from src.spira_integration.mapper.test_case_mapper import TestCaseMapper


@given('I have a test case mapper')
def step_have_mapper(context):
    """Create a test case mapper."""
    context.mapper = TestCaseMapper()


@when('I extract the test case ID from "{text}"')
def step_extract_tc_id_from_text(context, text):
    """Extract TC ID from text."""
    context.tc_id = context.mapper.get_test_case_id(text)


@then('I should receive test case ID {tc_id:d}')
def step_verify_tc_id(context, tc_id):
    """Verify extracted TC ID."""
    assert context.tc_id == tc_id, f"Expected TC ID {tc_id}, got {context.tc_id}"


@then('I should receive None')
def step_verify_none(context):
    """Verify result is None."""
    result = getattr(context, 'tc_id', getattr(context, 'automation_id', None))
    assert result is None, f"Expected None, got {result}"


@given('I have Allure raw data with a testCaseId label value of "{value}"')
def step_have_allure_label_data(context, value):
    """Create raw data with testCaseId label."""
    context.raw_data = {
        'name': 'Test',
        'labels': [{'name': 'testCaseId', 'value': value}]
    }


@when('I extract the test case ID from the raw data')
def step_extract_tc_id_from_raw(context):
    """Extract TC ID from raw data."""
    context.tc_id = context.mapper.extract_test_case_id(context.raw_data)


@given('I have raw data with fullName "{full_name}"')
def step_have_raw_data_fullname(context, full_name):
    """Create raw data with fullName."""
    context.raw_data = {'name': 'Test', 'fullName': full_name}


@given('I have Allure raw data with testCaseId "{hash_value}"')
def step_have_allure_testcaseid(context, hash_value):
    """Create raw data with top-level testCaseId."""
    context.raw_data = {
        'name': 'Test',
        'testCaseId': hash_value
    }


@when('I extract the automation ID')
def step_extract_automation_id(context):
    """Extract automation ID from raw data."""
    context.automation_id = context.mapper.extract_automation_id(context.raw_data)


@then('I should receive "{value}"')
def step_verify_string_value(context, value):
    """Verify string result."""
    result = getattr(context, 'automation_id', None)
    assert result == value, f"Expected '{value}', got '{result}'"


@given('I have JUnit raw data with classname "{classname}" and name "{name}"')
def step_have_junit_raw_data(context, classname, name):
    """Create JUnit-style raw data."""
    context.raw_data = {'classname': classname, 'name': name}


@given('I have ExtentReports raw data with name "{name}"')
def step_have_extent_raw_data(context, name):
    """Create ExtentReports-style raw data."""
    context.raw_data = {'name': name, 'extent_report': True}


@given('I have empty raw data')
def step_have_empty_raw_data(context):
    """Create empty raw data."""
    context.raw_data = {}
