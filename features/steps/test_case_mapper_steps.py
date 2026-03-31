"""Step definitions for test case mapper feature (07)."""

from behave import given, when, then
from src.spira_integration.mapper.test_case_mapper import TestCaseMapper


@given('I have a test case mapper')
def step_have_mapper(context):
    context.mapper = TestCaseMapper()


@when('I extract the test case ID from "{text}"')
def step_extract_tc_id_from_text(context, text):
    context.tc_id = context.mapper.get_test_case_id(text)


@then('I should receive test case ID {tc_id:d}')
def step_verify_tc_id(context, tc_id):
    assert context.tc_id == tc_id, f"Expected TC ID {tc_id}, got {context.tc_id}"


@then('I should receive None')
def step_verify_none(context):
    result = getattr(context, 'tc_id', getattr(context, 'automation_id', None))
    assert result is None, f"Expected None, got {result}"


@given('I have Allure raw data with a testCaseId label value of "{value}"')
def step_have_allure_label_data(context, value):
    context.raw_data = {
        'name': 'Test',
        'labels': [{'name': 'testCaseId', 'value': value}]
    }


@when('I extract the test case ID from the raw data')
def step_extract_tc_id_from_raw(context):
    context.tc_id = context.mapper.extract_test_case_id(context.raw_data)


@given('I have raw data with fullName "{full_name}"')
def step_have_raw_data_fullname(context, full_name):
    context.raw_data = {'name': 'Test', 'fullName': full_name}


@given('I have Allure raw data with testCaseId "{hash_value}"')
def step_have_allure_testcaseid(context, hash_value):
    context.raw_data = {'name': 'Test', 'testCaseId': hash_value}


@then('I should receive "{value}"')
def step_verify_string_value(context, value):
    result = getattr(context, 'automation_id', None)
    assert result == value, f"Expected '{value}', got '{result}'"


@given('I have JUnit raw data with classname "{classname}" and name "{name}"')
def step_have_junit_raw_data(context, classname, name):
    context.raw_data = {'classname': classname, 'name': name}


@given('I have ExtentReports raw data with name "{name}"')
def step_have_extent_raw_data(context, name):
    context.raw_data = {'name': name, 'extent_report': True}


@given('I have empty raw data')
def step_have_empty_raw_data(context):
    context.raw_data = {}
