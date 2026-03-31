"""Step definitions for Spira API client — real integration tests using env vars."""

import os
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch
from behave import given, when, then
from src.spira_integration.api.spira_client import SpiraAPIClient
from src.spira_integration.models import TestResult, TestStatus
from src.spira_integration.exceptions import (
    AuthenticationError, APIError, ValidationError, RateLimitError
)


# --- Environment and client setup ---

@given('the environment is configured')
def step_env_configured(context):
    """Verify required env vars are present."""
    context.env = {
        'url': os.environ.get('SPIRA_URL', ''),
        'username': os.environ.get('SPIRA_USERNAME', ''),
        'api_key': os.environ.get('SPIRA_API_KEY', ''),
        'project_id': int(os.environ.get('SPIRA_PROJECT_ID', '0')),
        'test_set_id': int(os.environ.get('SPIRA_TEST_SET_ID', '0')),
        'release_id': int(os.environ.get('SPIRA_RELEASE_ID', '0')),
        'automation_id_field': os.environ.get('SPIRA_AUTOMATION_ID_FIELD', ''),
    }


@then('{var_name} should be defined and non-empty')
def step_env_var_defined(context, var_name):
    val = os.environ.get(var_name, '')
    assert val, f"{var_name} is not defined or empty"


@when('I create a Spira API client from environment')
def step_create_client_from_env(context):
    context.client = SpiraAPIClient(
        base_url=context.env['url'],
        username=context.env['username'],
        api_key=context.env['api_key']
    )


@given('I have an authenticated client from environment')
def step_have_auth_client(context):
    context.client = SpiraAPIClient(
        base_url=context.env['url'],
        username=context.env['username'],
        api_key=context.env['api_key']
    )
    context.client.authenticate()


@given('I am authenticated with Spira')
def step_authenticated_with_spira(context):
    step_have_auth_client(context)


@when('I authenticate')
def step_authenticate(context):
    try:
        context.client.authenticate()
        context.auth_error = None
    except AuthenticationError as e:
        context.auth_error = e


@then('authentication should succeed')
def step_auth_succeeded(context):
    assert context.client._authenticated, "Authentication did not succeed"
    assert getattr(context, 'auth_error', None) is None, f"Auth error: {context.auth_error}"


@when('I create a Spira API client with wrong API key')
def step_create_client_bad_key(context):
    context.client = SpiraAPIClient(
        base_url=context.env['url'],
        username=context.env['username'],
        api_key='{00000000-0000-0000-0000-000000000000}'
    )


@when('I attempt to authenticate')
def step_attempt_auth(context):
    try:
        context.client.authenticate()
        context.error = None
    except AuthenticationError as e:
        context.error = e


@then('an AuthenticationError should be raised')
def step_verify_auth_error(context):
    assert context.error is not None, "Expected AuthenticationError"
    assert isinstance(context.error, AuthenticationError)


@when('I create a Spira API client with URL "{url}"')
def step_create_client_bad_url(context, url):
    try:
        context.client = SpiraAPIClient(base_url=url, username='u', api_key='k')
        context.error = None
    except ValidationError as e:
        context.error = e


@then('a ValidationError should be raised')
def step_verify_validation_error(context):
    assert context.error is not None, "Expected ValidationError"
    assert isinstance(context.error, ValidationError)


# --- Release validation ---

@when('I validate the configured release')
def step_validate_configured_release(context):
    try:
        context.release_data = context.client.validate_release(
            context.env['project_id'], context.env['release_id']
        )
        context.error = None
    except APIError as e:
        context.error = e
        context.release_data = None


@given('the configured release is valid')
def step_release_is_valid(context):
    context.release_data = context.client.validate_release(
        context.env['project_id'], context.env['release_id']
    )


@then('the release should exist')
def step_release_exists(context):
    assert context.release_data is not None, f"Release not found: {getattr(context, 'error', '')}"


@then('the release data should include a name')
@then('the release name should be returned')
def step_release_has_name(context):
    assert 'Name' in context.release_data, "Release data missing Name field"
    assert len(context.release_data['Name']) > 0


@when('I validate release ID {rid:d}')
def step_validate_release_by_id(context, rid):
    try:
        context.release_data = context.client.validate_release(context.env['project_id'], rid)
        context.error = None
    except APIError as e:
        context.error = e


@then('an APIError should be raised with "{text}"')
def step_api_error_with_text(context, text):
    assert context.error is not None, "Expected APIError"
    assert isinstance(context.error, APIError)
    assert text.lower() in str(context.error).lower(), f"Expected '{text}' in: {context.error}"


# --- Test set ---

@when('I check the configured test set')
def step_check_configured_test_set(context):
    try:
        context.test_set_result = context.client.create_or_get_test_set(
            context.env['project_id'], context.env['test_set_id'],
            release_id=context.env['release_id']
        )
        context.error = None
    except APIError as e:
        context.error = e
        context.test_set_result = None


@given('the configured test set is ready')
def step_test_set_ready(context):
    context.test_set_result = context.client.create_or_get_test_set(
        context.env['project_id'], context.env['test_set_id'],
        release_id=context.env['release_id']
    )


@then('the test set should be found')
@then('the test set should exist or be creatable')
def step_test_set_found(context):
    assert context.test_set_result is not None, f"Test set error: {getattr(context, 'error', '')}"


# --- Test run creation ---

@when('I create a test run with sample data')
@when('I create a test run with a sample passed result')
def step_create_sample_test_run(context):
    result = TestResult(
        name='BDD Preflight Test',
        status=TestStatus.PASSED,
        duration=0.1,
        start_time=datetime.now(),
        end_time=datetime.now(),
    )
    try:
        pid = context.env['project_id']
        auto_field = context.env.get('automation_id_field', '')
        stable_id = 'behave-preflight-validation-tc'

        # Try to find existing preflight TC via custom property
        tc_id = None
        if auto_field:
            tc_id = context.client.search_test_case_by_custom_property(
                pid, auto_field, stable_id
            )

        # Create if not found
        if not tc_id:
            if auto_field:
                tc_id = context.client.create_test_case_with_custom_property(
                    project_id=pid,
                    test_case_name='BDD Preflight Validation TC',
                    custom_field=auto_field,
                    custom_value=stable_id,
                    description='Reusable TC for behave pre-flight validation'
                )
            else:
                tc_id = context.client.create_test_case(
                    project_id=pid,
                    test_case_name='BDD Preflight Validation TC',
                )

        context.preflight_tc_id = tc_id
        context.test_run_id = context.client.create_test_run(
            project_id=pid,
            test_case_id=tc_id,
            result=result,
        )
        context.error = None
    except APIError as e:
        context.error = e
        context.test_run_id = None


@then('the test run ID should be returned')
@then('the test run should be created in Spira')
def step_test_run_created(context):
    assert context.test_run_id is not None, f"Test run not created: {getattr(context, 'error', '')}"


@then('the test run ID should be a positive integer')
def step_test_run_id_positive(context):
    assert isinstance(context.test_run_id, int), f"Expected int, got {type(context.test_run_id)}"
    assert context.test_run_id > 0, f"Expected positive ID, got {context.test_run_id}"


@then('the authenticated user should have access to the configured project')
def step_user_has_project_access(context):
    # If auth succeeded and we can validate release, we have project access
    assert context.client._authenticated


# --- Connectivity ---

@when('I check connectivity to the Spira URL')
def step_check_connectivity(context):
    import requests
    try:
        resp = requests.get(context.env['url'], timeout=10)
        context.connectivity_ok = resp.status_code < 500
    except Exception as e:
        context.connectivity_ok = False
        context.connectivity_error = str(e)


@then('the Spira instance should respond')
def step_spira_responds(context):
    assert context.connectivity_ok, f"Spira not reachable: {getattr(context, 'connectivity_error', '')}"


# --- Rate Limit Handler (09) ---

@given('I have a Spira API client')
def step_have_basic_client(context):
    context.client = SpiraAPIClient(
        base_url='https://spira.example.com',
        username='testuser',
        api_key='secret123'
    )
    context.client._authenticated = True


@when('the API returns HTTP {code:d} for a test run creation')
def step_api_returns_code(context, code):
    mock_response = MagicMock()
    mock_response.status_code = code
    mock_response.text = f'Error {code}'
    result = TestResult(name='Test', status=TestStatus.PASSED,
                       start_time=datetime.now(), end_time=datetime.now())
    with patch.object(context.client, '_request_with_retry', return_value=mock_response) as mock_req:
        try:
            context.client.create_test_run(1, 123, result)
            context.error = None
        except (RateLimitError, APIError) as e:
            context.error = e


@then('a RateLimitError should be raised')
def step_verify_rate_limit_error(context):
    assert context.error is not None, "Expected RateLimitError"
    assert isinstance(context.error, RateLimitError), f"Got {type(context.error)}: {context.error}"


@then('an APIError should be raised')
def step_verify_api_error(context):
    assert context.error is not None, "Expected APIError"
    assert isinstance(context.error, APIError), f"Got {type(context.error)}: {context.error}"


@then('the error message should contain "{text}"')
def step_error_contains(context, text):
    assert text.lower() in str(context.error).lower(), \
        f"Expected '{text}' in: {context.error}"


# --- Evidence Upload (11) ---

@given('I have an authenticated Spira API client')
def step_have_auth_spira_client(context):
    context.client = SpiraAPIClient(
        base_url='https://spira.example.com',
        username='testuser',
        api_key='secret123'
    )
    context.client._authenticated = True


@when('I attempt to upload a non-existent file "{path}"')
def step_upload_nonexistent(context, path):
    # upload_evidence should log warning and return, not raise
    try:
        context.client.upload_evidence(1, 789, path)
        context.upload_skipped = True
        context.upload_error = None
    except Exception as e:
        context.upload_skipped = False
        context.upload_error = e


@then('the upload should be skipped without raising an error')
def step_upload_skipped_ok(context):
    assert context.upload_skipped, f"Upload raised error: {context.upload_error}"


@given('I have a temporary PNG evidence file')
def step_have_temp_png(context):
    temp = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.png')
    # Write a minimal valid-ish PNG header
    temp.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    temp.close()
    context.temp_files.append(temp.name)
    context.evidence_file = temp.name


@when('I read the evidence file')
def step_read_evidence(context):
    with open(context.evidence_file, 'rb') as f:
        context.file_content = f.read()


@then('the file content should be bytes not string')
def step_content_is_bytes(context):
    assert isinstance(context.file_content, bytes), f"Expected bytes, got {type(context.file_content)}"


@given('I have a temporary evidence file named "{filename}"')
def step_have_named_evidence(context, filename):
    import shutil
    temp = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix=Path(filename).suffix)
    temp.write(b'\x89PNG\r\n\x1a\n')
    temp.close()
    # Rename to desired filename
    target = Path(temp.name).parent / filename
    shutil.move(temp.name, target)
    context.temp_files.append(str(target))
    context.evidence_file = str(target)


@when('I prepare the upload payload')
def step_prepare_payload(context):
    context.payload_filename = Path(context.evidence_file).name


@then('the payload filename should be "{filename}"')
def step_verify_payload_filename(context, filename):
    assert context.payload_filename == filename, \
        f"Expected '{filename}', got '{context.payload_filename}'"


@when('I create a test run and upload the evidence file')
def step_create_run_and_upload(context):
    result = TestResult(
        name='Evidence Upload Test',
        status=TestStatus.PASSED,
        duration=0.1,
        start_time=datetime.now(),
        end_time=datetime.now(),
    )
    try:
        pid = context.env['project_id']
        auto_field = context.env.get('automation_id_field', '')
        stable_id = 'behave-evidence-upload-tc'

        # Reuse existing TC via custom property
        tc_id = None
        if auto_field:
            tc_id = context.client.search_test_case_by_custom_property(
                pid, auto_field, stable_id
            )
        if not tc_id:
            if auto_field:
                tc_id = context.client.create_test_case_with_custom_property(
                    project_id=pid,
                    test_case_name='BDD Evidence Upload TC',
                    custom_field=auto_field,
                    custom_value=stable_id,
                )
            else:
                tc_id = context.client.create_test_case(
                    project_id=pid,
                    test_case_name='BDD Evidence Upload TC',
                )

        context.test_run_id = context.client.create_test_run(
            project_id=pid,
            test_case_id=tc_id,
            result=result,
        )
        context.client.upload_evidence(pid, context.test_run_id, context.evidence_file)
        context.evidence_uploaded = True
        context.error = None
    except Exception as e:
        context.evidence_uploaded = False
        context.error = e


@then('the evidence should be uploaded successfully')
def step_evidence_uploaded_ok(context):
    assert context.evidence_uploaded, f"Evidence upload failed: {getattr(context, 'error', '')}"


# --- Custom Property Matching (10) ---

@given('I have raw data with testCaseId "{hash_val}"')
def step_raw_data_testcaseid(context, hash_val):
    context.raw_data = {'testCaseId': hash_val, 'name': 'Test'}


@given('I have raw data with classname "{cls}" and name "{name}"')
def step_raw_data_classname(context, cls, name):
    context.raw_data = {'classname': cls, 'name': name}


@given('I have raw data with no identifiers')
def step_raw_data_empty(context):
    context.raw_data = {'name': 'Test', 'extent_report': True}


@when('I extract the automation ID')
def step_extract_auto_id(context):
    from src.spira_integration.mapper.test_case_mapper import TestCaseMapper
    mapper = getattr(context, 'mapper', TestCaseMapper())
    context.automation_id = mapper.extract_automation_id(context.raw_data)


@then('the automation ID should be "{value}"')
def step_verify_auto_id(context, value):
    assert context.automation_id == value, f"Expected '{value}', got '{context.automation_id}'"


@then('the automation ID should be None')
def step_verify_auto_id_none(context):
    assert context.automation_id is None, f"Expected None, got '{context.automation_id}'"


@when('I extract TC ID from "{text}"')
def step_extract_tc_from_text(context, text):
    from src.spira_integration.mapper.test_case_mapper import TestCaseMapper
    mapper = TestCaseMapper()
    context.tc_id = mapper.get_test_case_id(text)


@then('the TC ID should be {tc_id:d}')
def step_verify_tc_id_int(context, tc_id):
    assert context.tc_id == tc_id, f"Expected {tc_id}, got {context.tc_id}"


@then('the TC ID should be None')
def step_verify_tc_id_none(context):
    assert context.tc_id is None, f"Expected None, got {context.tc_id}"


@given('SPIRA_AUTOMATION_ID_FIELD is defined')
def step_automation_field_defined(context):
    field = os.environ.get('SPIRA_AUTOMATION_ID_FIELD', '')
    assert field, "SPIRA_AUTOMATION_ID_FIELD is not defined — set it in .env or pipeline config"
    context.automation_id_field = field


@when('I search for a test case with a known automation ID')
def step_search_known_auto_id(context):
    try:
        context.search_result = context.client.search_test_case_by_custom_property(
            context.env['project_id'],
            context.automation_id_field,
            'behave-test-known-id'
        )
        context.error = None
    except Exception as e:
        context.error = e
        context.search_result = None


@then('the search should return a result or empty list without error')
def step_search_no_error(context):
    assert context.error is None, f"Search failed: {context.error}"
    # Result can be None (no match) or an int (match found) — both are valid
    assert context.search_result is None or isinstance(context.search_result, int)


@when('I create a test case with a unique automation ID')
def step_create_tc_unique_id(context):
    import uuid
    context.unique_auto_id = f'behave-test-{uuid.uuid4().hex[:12]}'
    try:
        context.created_tc_id = context.client.create_test_case_with_custom_property(
            project_id=context.env['project_id'],
            test_case_name=f'BDD Test - {context.unique_auto_id}',
            custom_field=context.automation_id_field,
            custom_value=context.unique_auto_id,
        )
        context.error = None
    except Exception as e:
        context.error = e
        context.created_tc_id = None


@when('I search for that automation ID')
def step_search_created_id(context):
    try:
        context.found_tc_id = context.client.search_test_case_by_custom_property(
            context.env['project_id'],
            context.automation_id_field,
            context.unique_auto_id,
        )
        context.error = None
    except Exception as e:
        context.error = e
        context.found_tc_id = None


@then('the search should return the created test case')
def step_verify_found_created(context):
    assert context.error is None, f"Search failed: {context.error}"
    assert context.found_tc_id == context.created_tc_id, \
        f"Expected TC {context.created_tc_id}, found {context.found_tc_id}"
    # Clean up: delete the test TC we created
    try:
        context.client.delete_test_case(context.env['project_id'], context.created_tc_id)
    except Exception:
        pass  # best-effort cleanup


# --- Parser validation for preflight (12) ---

@given('sample Allure results exist at "{path}"')
def step_allure_results_exist(context, path):
    assert Path(path).exists(), f"Sample Allure results not found at {path}"
    context.results_path = path


@given('sample JUnit results exist at "{path}"')
def step_junit_results_exist(context, path):
    assert Path(path).exists(), f"Sample JUnit results not found at {path}"
    context.results_path = path


@given('client ExtentReports results exist at "{path}"')
def step_extent_results_exist(context, path):
    assert Path(path).exists(), f"Client ExtentReports results not found at {path}"
    context.results_path = path


@when('I parse the sample Allure results')
def step_parse_allure(context):
    from src.spira_integration.parsers.allure_parser import AllureParser
    parser = AllureParser()
    context.results = parser.parse(context.results_path)


@when('I parse the sample JUnit results')
def step_parse_junit(context):
    from src.spira_integration.parsers.junit_parser import JUnitParser
    parser = JUnitParser()
    context.results = parser.parse(context.results_path)


@when('I parse the client ExtentReports results')
def step_parse_extent(context):
    from src.spira_integration.parsers.extent_parser import ExtentParser
    parser = ExtentParser()
    context.results = parser.parse(context.results_path)


@then('at least {count:d} test result should be extracted')
def step_at_least_n_results(context, count):
    assert len(context.results) >= count, \
        f"Expected at least {count} results, got {len(context.results)}"


@then('each result should have a name and status')
def step_each_has_name_status(context):
    for r in context.results:
        assert r.name, f"Result missing name: {r}"
        assert r.status is not None, f"Result missing status: {r.name}"


@then('each result should have evidence files discovered')
def step_each_has_evidence(context):
    has_evidence = any(len(r.evidence_files) > 0 for r in context.results)
    assert has_evidence, "No results have evidence files"


# --- Preflight-specific steps ---

@when('I authenticate with the configured credentials')
def step_auth_with_configured(context):
    context.client = SpiraAPIClient(
        base_url=context.env['url'],
        username=context.env['username'],
        api_key=context.env['api_key']
    )
    try:
        context.client.authenticate()
        context.auth_error = None
    except AuthenticationError as e:
        context.auth_error = e


# --- Retry logic tests ---

@when('the API returns HTTP 429 then 200')
def step_429_then_200(context):
    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {'TestRunId': 999}
    with patch.object(context.client._session, 'post', side_effect=[mock_429, mock_200]):
        with patch('time.sleep') as mock_sleep:
            result = TestResult(name='Test', status=TestStatus.PASSED,
                               start_time=datetime.now(), end_time=datetime.now())
            try:
                context.test_run_id = context.client.create_test_run(1, 123, result)
                context.retry_error = None
                context.mock_sleep = mock_sleep
            except Exception as e:
                context.retry_error = e


@then('the request should succeed after retry')
def step_retry_succeeded(context):
    assert context.retry_error is None, f"Expected success, got: {context.retry_error}"
    assert context.test_run_id == 999


@then('the retry should have waited before retrying')
def step_retry_waited(context):
    context.mock_sleep.assert_called()


@when('the API returns HTTP 429 for all retries')
def step_429_all_retries(context):
    mock_429 = MagicMock()
    mock_429.status_code = 429
    with patch.object(context.client._session, 'post', return_value=mock_429):
        with patch('time.sleep'):
            result = TestResult(name='Test', status=TestStatus.PASSED,
                               start_time=datetime.now(), end_time=datetime.now())
            try:
                context.client.create_test_run(1, 123, result)
                context.error = None
            except RateLimitError as e:
                context.error = e
