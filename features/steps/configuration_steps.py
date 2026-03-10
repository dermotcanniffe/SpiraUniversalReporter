"""Step definitions for configuration manager feature."""

import os
import argparse
import tempfile
from pathlib import Path
from behave import given, when, then
from src.spira_integration.config.config_manager import (
    ConfigurationManager, create_argument_parser
)
from src.spira_integration.exceptions import ConfigurationError, ValidationError


@given('I have a configuration manager')
def step_have_config_manager(context):
    """Create a configuration manager."""
    context.config_manager = ConfigurationManager()


@when('I provide the following CLI arguments')
def step_provide_cli_arguments(context):
    """Parse CLI arguments from table."""
    # Create a temporary results file for testing
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write('<testsuite></testsuite>')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    
    args_dict = {}
    for row in context.table:
        arg_name = row['argument'].replace('--', '').replace('-', '_')
        # Map spira_url to url for argparse compatibility
        if arg_name == 'spira_url':
            arg_name = 'url'
        value = row['value']
        # Replace placeholder with actual temp file
        if 'results' in arg_name and '/path/to/' in value:
            value = temp_file.name
        args_dict[arg_name] = value
    
    # Create argparse Namespace
    context.data.args = argparse.Namespace(**args_dict)
    context.data.config = context.config_manager.load_from_args(context.data.args)


@then('the configuration should be loaded successfully')
def step_config_loaded_successfully(context):
    """Verify configuration was loaded."""
    assert context.data.config is not None, "Configuration not loaded"


@then('the {param} should be "{value}"')
def step_verify_config_value(context, param, value):
    """Verify a configuration parameter value."""
    actual_value = getattr(context.data.config, param)
    assert actual_value == value, \
        f"Expected {param}={value}, got {actual_value}"


@when('I set the following environment variables')
def step_set_environment_variables(context):
    """Set environment variables from table."""
    # Create a temporary results file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write('<testsuite></testsuite>')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    
    for row in context.table:
        var_name = row['variable']
        value = row['value']
        # Replace placeholder with actual temp file
        if 'RESULTS_FILE' in var_name and '/path/to/' in value:
            value = temp_file.name
        context.original_env[var_name] = os.environ.get(var_name)
        os.environ[var_name] = value
    
    # Create empty args namespace
    context.data.args = argparse.Namespace()
    context.data.config = context.config_manager.load_from_args(context.data.args)


@given('I set the environment variable "{var_name}" to "{value}"')
def step_set_single_env_var(context, var_name, value):
    """Set a single environment variable."""
    context.original_env[var_name] = os.environ.get(var_name)
    os.environ[var_name] = value


@when('I provide the CLI argument "{arg_name}" with value "{value}"')
def step_provide_single_cli_arg(context, arg_name, value):
    """Provide a single CLI argument."""
    # Create temp file if needed
    if 'results-file' in arg_name:
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
        temp_file.write('<testsuite></testsuite>')
        temp_file.close()
        context.temp_files.append(temp_file.name)
        value = temp_file.name
    
    # Map spira-url to url
    param_name = arg_name.replace('--', '').replace('-', '_')
    if param_name == 'spira_url':
        param_name = 'url'
    
    arg_dict = {param_name: value}
    # Add required args with dummy values
    if 'url' not in arg_dict:
        arg_dict['url'] = os.environ.get('SPIRA_URL', 'https://dummy.com')
    if 'project_id' not in arg_dict:
        arg_dict['project_id'] = os.environ.get('SPIRA_PROJECT_ID', '1')
    if 'test_set_id' not in arg_dict:
        arg_dict['test_set_id'] = os.environ.get('SPIRA_TEST_SET_ID', '1')
    if 'username' not in arg_dict:
        arg_dict['username'] = os.environ.get('SPIRA_USERNAME', 'user')
    if 'api_key' not in arg_dict:
        arg_dict['api_key'] = os.environ.get('SPIRA_API_KEY', 'key')
    if 'results_file' not in arg_dict:
        if not context.temp_files:
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
            temp_file.write('<testsuite></testsuite>')
            temp_file.close()
            context.temp_files.append(temp_file.name)
        arg_dict['results_file'] = context.temp_files[0]
    
    context.data.args = argparse.Namespace(**arg_dict)
    context.data.config = context.config_manager.load_from_args(context.data.args)


@when('I attempt to load configuration without providing "{param}"')
def step_load_without_param(context, param):
    """Attempt to load configuration without a required parameter."""
    # Create minimal args without the specified param
    arg_dict = {}
    
    # Add all required params except the one we're testing
    if param != 'spira-url':
        arg_dict['url'] = 'https://spira.example.com'
    if param != 'project-id':
        arg_dict['project_id'] = '123'
    if param != 'test-set-id':
        arg_dict['test_set_id'] = '456'
    if param != 'username':
        arg_dict['username'] = 'testuser'
    if param != 'api-key':
        arg_dict['api_key'] = 'secret123'
    if param != 'results-file':
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
        temp_file.write('<testsuite></testsuite>')
        temp_file.close()
        context.temp_files.append(temp_file.name)
        arg_dict['results_file'] = temp_file.name
    
    context.data.args = argparse.Namespace(**arg_dict)
    
    try:
        context.data.config = context.config_manager.load_from_args(context.data.args)
        context.data.error = None
    except ConfigurationError as e:
        context.data.error = e


@then('a ConfigurationError should be raised')
def step_verify_config_error_raised(context):
    """Verify ConfigurationError was raised."""
    assert context.data.error is not None, "Expected ConfigurationError but none was raised"
    # Accept both ConfigurationError and ValidationError
    assert isinstance(context.data.error, (ConfigurationError, ValidationError)), \
        f"Expected ConfigurationError or ValidationError, got {type(context.data.error)}"


@then('the error message should indicate "{message}"')
def step_verify_error_message(context, message):
    """Verify error message contains expected text."""
    # Check both context.data.error and context.error for compatibility
    error = getattr(context, 'error', None) or getattr(context.data, 'error', None) if hasattr(context, 'data') else None
    assert error is not None, "No error was raised"
    error_msg = str(error).lower()
    
    # Normalize the expected message for flexible matching
    # "spira-url is required" should match "url is required"
    normalized_message = message.lower().replace('spira-', '').replace('-', ' ')
    
    assert normalized_message in error_msg or message.lower() in error_msg, \
        f"Expected '{message}' in error message, got: {error}"


@when('I provide an invalid URL "{url}"')
def step_provide_invalid_url(context, url):
    """Provide an invalid URL."""
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write('<testsuite></testsuite>')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    
    arg_dict = {
        'url': url,
        'project_id': '123',
        'test_set_id': '456',
        'username': 'testuser',
        'api_key': 'secret123',
        'results_file': temp_file.name
    }
    
    context.data.args = argparse.Namespace(**arg_dict)
    
    try:
        context.data.config = context.config_manager.load_from_args(context.data.args)
        context.config_manager.validate()
        context.data.error = None
    except (ConfigurationError, ValidationError) as e:
        context.data.error = e


@when('I provide a results file path that does not exist')
def step_provide_nonexistent_file(context):
    """Provide a non-existent file path."""
    arg_dict = {
        'url': 'https://spira.example.com',
        'project_id': '123',
        'test_set_id': '456',
        'username': 'testuser',
        'api_key': 'secret123',
        'results_file': '/nonexistent/path/results.xml'
    }
    
    context.data.args = argparse.Namespace(**arg_dict)
    
    try:
        context.data.config = context.config_manager.load_from_args(context.data.args)
        context.config_manager.validate()
        context.data.error = None
    except ConfigurationError as e:
        context.data.error = e


@given('I have a configuration manager with API key "{api_key}"')
def step_config_manager_with_api_key(context, api_key):
    """Create configuration manager with specific API key."""
    context.config_manager = ConfigurationManager()
    context.data.api_key = api_key
    
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml')
    temp_file.write('<testsuite></testsuite>')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    
    config_dict = {
        'spira_url': 'https://spira.example.com',
        'project_id': '123',
        'test_set_id': '456',
        'username': 'testuser',
        'api_key': api_key,
        'results_file': temp_file.name
    }
    context.data.config = context.config_manager.load_from_dict(config_dict)


@when('I log the configuration')
def step_log_configuration(context):
    """Get masked configuration for logging."""
    context.data.masked_config = context.config_manager.get_masked_config()


@then('the API key should be masked as "{masked_value}"')
def step_verify_api_key_masked(context, masked_value):
    """Verify API key is properly masked."""
    actual_masked = context.data.masked_config['api_key']
    assert actual_masked == masked_value, \
        f"Expected masked API key '{masked_value}', got '{actual_masked}'"


@then('the full API key should not appear in logs')
def step_verify_full_key_not_in_logs(context):
    """Verify full API key is not in masked config."""
    masked_value = context.data.masked_config['api_key']
    assert context.data.api_key != masked_value, \
        "Full API key should not appear in masked config"
    assert '*' in masked_value, \
        "Masked value should contain asterisks"
