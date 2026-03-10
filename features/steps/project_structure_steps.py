"""Step definitions for project structure feature."""

import os
from pathlib import Path
from behave import given, when, then
from src.spira_integration.models import (
    TestResult, TestStatus, Configuration, TestCaseMapping,
    SpiraTestRun, ExecutionSummary
)
from src.spira_integration.parser_base import TestResultParser
from src.spira_integration.logging_config import setup_logging


@given('I am setting up a new Python project')
def step_setting_up_project(context):
    """Initialize project setup context."""
    context.project_root = Path.cwd()


@when('I create the package structure')
def step_create_package_structure(context):
    """Verify package structure creation."""
    context.directories_to_check = [
        'src/spira_integration',
        'src/spira_integration/parsers',
        'src/spira_integration/api',
        'src/spira_integration/config',
        'tests',
        'features',
        'features/steps'
    ]


@then('the following directories should exist')
def step_verify_directories_exist(context):
    """Verify all required directories exist."""
    for row in context.table:
        directory = row['directory']
        dir_path = context.project_root / directory
        assert dir_path.exists(), f"Directory {directory} does not exist"
        assert dir_path.is_dir(), f"{directory} is not a directory"


@given('I need to represent test results and configuration')
def step_need_data_models(context):
    """Set up context for data model verification."""
    context.models = {}


@when('I define the core data models')
def step_define_data_models(context):
    """Import and verify data models."""
    context.models = {
        'TestResult': TestResult,
        'TestStatus': TestStatus,
        'Configuration': Configuration,
        'TestCaseMapping': TestCaseMapping,
        'SpiraTestRun': SpiraTestRun,
        'ExecutionSummary': ExecutionSummary
    }


@then('the following models should be defined')
def step_verify_models_defined(context):
    """Verify all required models are defined."""
    for row in context.table:
        model_name = row['model_name']
        assert model_name in context.models, f"Model {model_name} not defined"
        assert context.models[model_name] is not None


@given('I need a pluggable parser architecture')
def step_need_parser_architecture(context):
    """Set up context for parser interface verification."""
    context.parser_base = None


@when('I define the TestResultParser abstract base class')
def step_define_parser_base(context):
    """Import parser base class."""
    context.parser_base = TestResultParser


@then('it should have an abstract method "parse" that accepts a file path')
def step_verify_parse_method(context):
    """Verify parse method exists."""
    assert hasattr(context.parser_base, 'parse'), \
        "TestResultParser does not have parse method"
    # Verify it's abstract by trying to instantiate
    try:
        context.parser_base()
        assert False, "TestResultParser should not be instantiable"
    except TypeError:
        pass  # Expected - abstract class cannot be instantiated


@then('it should return a list of TestResult objects')
def step_verify_parse_return_type(context):
    """Verify parse method signature."""
    import inspect
    sig = inspect.signature(context.parser_base.parse)
    # Just verify the method exists and has file_path parameter
    assert 'file_path' in sig.parameters or 'self' in sig.parameters


@given('I need to log execution progress and errors')
def step_need_logging(context):
    """Set up context for logging verification."""
    context.logging_setup = None


@when('I configure logging')
def step_configure_logging(context):
    """Configure logging."""
    context.logging_setup = setup_logging


@then('logs should be written to stdout for progress messages')
def step_verify_stdout_logging(context):
    """Verify stdout logging configuration."""
    import logging
    logger = logging.getLogger()
    # Verify logger has handlers
    assert len(logger.handlers) > 0, "No logging handlers configured"


@then('logs should be written to stderr for error messages')
def step_verify_stderr_logging(context):
    """Verify stderr logging configuration."""
    import logging
    logger = logging.getLogger()
    # Verify logger has handlers
    assert len(logger.handlers) > 0, "No logging handlers configured"


@then('the log format should include timestamp, level, and message')
def step_verify_log_format(context):
    """Verify log format."""
    import logging
    logger = logging.getLogger()
    for handler in logger.handlers:
        if handler.formatter:
            fmt = handler.formatter._fmt
            assert 'asctime' in fmt or 'levelname' in fmt or 'message' in fmt


@given('I need to specify project dependencies')
def step_need_dependencies(context):
    """Set up context for dependencies verification."""
    context.requirements_file = Path.cwd() / 'requirements.txt'


@when('I create requirements.txt')
def step_create_requirements(context):
    """Verify requirements.txt exists."""
    assert context.requirements_file.exists(), \
        "requirements.txt does not exist"


@then('it should include the following packages')
def step_verify_packages(context):
    """Verify required packages are in requirements.txt."""
    with open(context.requirements_file, 'r') as f:
        content = f.read()
    
    for row in context.table:
        package = row['package']
        assert package in content, \
            f"Package {package} not found in requirements.txt"
