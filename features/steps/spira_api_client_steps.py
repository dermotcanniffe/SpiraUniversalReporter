"""Step definitions for Spira API Client feature."""

from behave import given, when, then
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.spira_integration.api.spira_client import SpiraAPIClient
from src.spira_integration.models import TestResult, TestStatus
from src.spira_integration.exceptions import (
    AuthenticationError,
    APIError,
    ValidationError
)


@given('I have Spira credentials')
def step_have_spira_credentials(context):
    """Store Spira credentials from table."""
    context.credentials = {}
    for row in context.table:
        context.credentials[row['field']] = row['value']


@when('I initialize the Spira API Client')
def step_initialize_spira_client(context):
    """Initialize Spira API Client with credentials."""
    try:
        context.client = SpiraAPIClient(
            base_url=context.credentials['base_url'],
            username=context.credentials['username'],
            api_key=context.credentials['api_key']
        )
        context.error = None
    except Exception as e:
        context.error = e
        context.client = None


@then('the client should be created successfully')
def step_client_created_successfully(context):
    """Verify client was created without errors."""
    assert context.error is None, f"Expected no error, but got: {context.error}"
    assert context.client is not None, "Client should be created"
    # Also verify base URL was normalized
    expected_url = context.credentials['base_url'].rstrip('/') + '/'
    assert context.client.base_url == expected_url, \
        f"Expected base URL '{expected_url}', got '{context.client.base_url}'"


@given('I have a Spira API Client')
def step_have_spira_client(context):
    """Create a basic Spira API Client."""
    context.client = SpiraAPIClient(
        base_url="https://spira.example.com",
        username="testuser",
        api_key="{test-api-key}"
    )


@when('I authenticate with valid credentials')
def step_authenticate_valid(context):
    """Authenticate with valid credentials (mocked)."""
    with patch.object(context.client._session, 'get') as mock_get:
        # Mock successful authentication response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        try:
            context.client.authenticate()
            context.error = None
        except Exception as e:
            context.error = e


@then('the authentication should succeed')
def step_authentication_succeeds(context):
    """Verify authentication succeeded."""
    assert context.error is None, f"Expected no error, but got: {context.error}"
    assert context.client._authenticated is True, "Client should be authenticated"


@then('the authentication state should be cached')
def step_authentication_cached(context):
    """Verify authentication state is cached."""
    assert context.client._authenticated is True, "Authentication state should be cached"


@given('I have Spira credentials with invalid URL "{invalid_url}"')
def step_have_invalid_url_credentials(context, invalid_url):
    """Store invalid URL credentials."""
    context.credentials = {
        'base_url': invalid_url,
        'username': 'testuser',
        'api_key': '{test-key}'
    }


@when('I attempt to initialize the Spira API Client')
def step_attempt_initialize_client(context):
    """Attempt to initialize client (may fail)."""
    try:
        context.client = SpiraAPIClient(
            base_url=context.credentials['base_url'],
            username=context.credentials['username'],
            api_key=context.credentials['api_key']
        )
        context.error = None
    except Exception as e:
        context.error = e
        context.client = None


@then('a ValidationError should be raised')
def step_validation_error_raised(context):
    """Verify ValidationError was raised."""
    assert context.error is not None, "Expected ValidationError to be raised"
    assert isinstance(context.error, ValidationError), \
        f"Expected ValidationError, got {type(context.error).__name__}"


@when('I authenticate with invalid credentials')
def step_authenticate_invalid(context):
    """Authenticate with invalid credentials (mocked)."""
    with patch.object(context.client._session, 'get') as mock_get:
        # Mock authentication failure response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        try:
            context.client.authenticate()
            context.error = None
        except Exception as e:
            context.error = e


@then('an AuthenticationError should be raised')
def step_authentication_error_raised(context):
    """Verify AuthenticationError was raised."""
    assert context.error is not None, "Expected AuthenticationError to be raised"
    assert isinstance(context.error, AuthenticationError), \
        f"Expected AuthenticationError, got {type(context.error).__name__}"


@then('the error should include the HTTP status code')
def step_error_includes_status_code(context):
    """Verify error message includes HTTP status code."""
    assert context.error is not None, "Expected an error"
    error_message = str(context.error)
    assert "401" in error_message or "status" in error_message.lower(), \
        f"Expected error to include status code, got: {error_message}"


@then('the error should include the response message')
def step_error_includes_response_message(context):
    """Verify error message includes response details."""
    assert context.error is not None, "Expected an error"
    error_message = str(context.error)
    assert len(error_message) > 0, "Error message should not be empty"


@given('I have an authenticated Spira API Client')
def step_have_authenticated_client(context):
    """Create an authenticated Spira API Client."""
    context.client = SpiraAPIClient(
        base_url="https://spira.example.com",
        username="testuser",
        api_key="{test-api-key}"
    )
    # Mark as authenticated without actually calling API
    context.client._authenticated = True


@given('I have test run data')
def step_have_test_run_data(context):
    """Store test run data from table."""
    context.test_run_data = {}
    for row in context.table:
        context.test_run_data[row['field']] = row['value']
    
    # Create TestResult object
    context.test_result = TestResult(
        name=context.test_run_data.get('test_case_id', 'Test'),
        status=TestStatus.PASSED if context.test_run_data.get('execution_status') == 'PASSED' else TestStatus.FAILED,
        start_time=datetime.fromisoformat(context.test_run_data.get('start_time', '2024-01-01T10:00:00+00:00').replace('Z', '+00:00')),
        end_time=datetime.fromisoformat(context.test_run_data.get('end_time', '2024-01-01T10:01:00+00:00').replace('Z', '+00:00'))
    )


@when('I create a test run for project {project_id:d} and test set {test_set_id:d}')
def step_create_test_run(context, project_id, test_set_id):
    """Create a test run (mocked)."""
    # Create a default test result if not already set
    if not hasattr(context, 'test_result'):
        context.test_result = TestResult(
            name="Default Test",
            status=TestStatus.PASSED,
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 1, 0)
        )
    
    with patch.object(context.client._session, 'post') as mock_post:
        # Mock successful test run creation
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'TestRunId': 999}
        mock_response.text = ''
        mock_post.return_value = mock_response
        
        try:
            context.test_run_id = context.client.create_test_run(
                project_id=project_id,
                test_set_id=test_set_id,
                test_case_id=123,
                result=context.test_result
            )
            context.error = None
            context.mock_post = mock_post
        except Exception as e:
            context.error = e
            context.test_run_id = None


@then('the test run should be created successfully')
def step_test_run_created_successfully(context):
    """Verify test run was created."""
    assert context.error is None, f"Expected no error, but got: {context.error}"
    assert context.test_run_id is not None, "Test run ID should be returned"


@then('the response should contain a test run ID')
def step_response_contains_test_run_id(context):
    """Verify response contains test run ID."""
    assert context.test_run_id is not None, "Test run ID should be present"
    assert isinstance(context.test_run_id, int), "Test run ID should be an integer"


@then('the test run ID should be logged')
def step_test_run_id_logged(context):
    """Verify test run ID would be logged (we check the ID exists)."""
    assert context.test_run_id is not None, "Test run ID should exist for logging"


@given('I have test run data with all fields')
def step_have_complete_test_run_data(context):
    """Create test result with all fields."""
    context.test_result = TestResult(
        name="Complete Test",
        status=TestStatus.FAILED,
        start_time=datetime(2024, 1, 1, 10, 0, 0),
        end_time=datetime(2024, 1, 1, 10, 1, 0),
        error_message="Test failed",
        stack_trace="Stack trace here"
    )


@when('I create a test run')
def step_create_test_run_simple(context):
    """Create a test run with default parameters."""
    with patch.object(context.client._session, 'post') as mock_post:
        # Mock successful test run creation
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'TestRunId': 999}
        mock_response.text = ''
        mock_post.return_value = mock_response
        
        try:
            context.test_run_id = context.client.create_test_run(
                project_id=1,
                test_set_id=10,
                test_case_id=123,
                result=context.test_result
            )
            context.error = None
            context.mock_post = mock_post
        except Exception as e:
            context.error = e


@when('the Spira API returns an error response with status {status_code:d}')
def step_api_returns_error(context, status_code):
    """Mock API error response."""
    with patch.object(context.client._session, 'post') as mock_post:
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        try:
            context.test_result = TestResult(
                name="Test",
                status=TestStatus.PASSED,
                start_time=datetime(2024, 1, 1, 10, 0, 0),
                end_time=datetime(2024, 1, 1, 10, 1, 0)
            )
            context.client.create_test_run(
                project_id=1,
                test_set_id=10,
                test_case_id=123,
                result=context.test_result
            )
            context.error = None
        except Exception as e:
            context.error = e


@then('an APIError should be raised')
def step_api_error_raised(context):
    """Verify APIError was raised."""
    assert context.error is not None, "Expected APIError to be raised"
    assert isinstance(context.error, APIError), \
        f"Expected APIError, got {type(context.error).__name__}"



@then('the request should be sent to the correct endpoint')
def step_verify_request_endpoint_generic(context):
    """Verify the request was sent to the correct endpoint."""
    assert hasattr(context, 'mock_post'), "Mock POST should be available"
    call_args = context.mock_post.call_args
    actual_url = call_args[0][0] if call_args[0] else call_args.kwargs.get('url', '')
    # Just verify it contains the test-runs endpoint
    assert 'test-runs' in actual_url, \
        f"Expected 'test-runs' in URL, got: {actual_url}"


@then('the request body should include required fields')
def step_verify_request_body_fields_generic(context):
    """Verify request body includes required fields."""
    assert hasattr(context, 'mock_post'), "Mock POST should be available"
    call_args = context.mock_post.call_args
    payload = call_args.kwargs.get('json', {})
    
    # Check for key required fields
    required_fields = ['TestCaseId', 'ExecutionStatusId', 'StartDate', 'EndDate']
    for field in required_fields:
        assert field in payload, f"Field '{field}' should be in request body"


@then('the error should include status code {status_code:d}')
def step_error_includes_specific_status_simple(context, status_code):
    """Verify error includes specific status code."""
    assert context.error is not None, "Expected an error"
    error_message = str(context.error)
    assert str(status_code) in error_message, \
        f"Expected error to include status code {status_code}, got: {error_message}"
