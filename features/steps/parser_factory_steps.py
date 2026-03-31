"""Step definitions for parser factory feature - keeping it simple and atomic."""

import tempfile
from pathlib import Path
from behave import given, when, then
from src.spira_integration.parsers.parser_factory import ParserFactory
from src.spira_integration.exceptions import UnsupportedFormatError


@given('I have a parser factory')
def step_have_parser_factory(context):
    """Create a parser factory."""
    context.factory = ParserFactory()


@when('I request a parser for type "{result_type}"')
def step_request_parser(context, result_type):
    """Request a parser for a specific type."""
    try:
        context.parser = context.factory.get_parser(result_type)
        context.error = None
    except UnsupportedFormatError as e:
        context.error = e
        context.parser = None


@then('I should receive a {parser_class} instance')
@then('I should receive an {parser_class} instance')
def step_verify_parser_instance(context, parser_class):
    """Verify the parser instance type."""
    assert context.parser is not None, "No parser was returned"
    assert context.parser.__class__.__name__ == parser_class, \
        f"Expected {parser_class}, got {context.parser.__class__.__name__}"


@given('I have a file named "{filename}"')
def step_have_file_named(context, filename):
    """Create a temporary file with the given name."""
    # Create temp file with specific extension
    suffix = Path(filename).suffix
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix=suffix
    )
    
    # Write appropriate content based on extension
    if suffix == '.xml':
        temp_file.write('<?xml version="1.0"?><testsuite></testsuite>')
    elif suffix == '.json':
        temp_file.write('{"uuid": "test-1", "status": "passed"}')
    
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@when('I detect the result type')
def step_detect_result_type(context):
    """Detect result type from file."""
    try:
        context.detected_type = context.factory.detect_result_type(context.test_file)
        context.error = None
    except UnsupportedFormatError as e:
        context.error = e
        context.detected_type = None


@then('it detects "{expected_type}"')
def step_verify_detected_type(context, expected_type):
    """Verify the detected type."""
    assert context.detected_type == expected_type, \
        f"Expected {expected_type}, got {context.detected_type}"


@given('I have a file with XML content starting with "{content}"')
def step_have_xml_file_with_content(context, content):
    """Create XML file with specific content."""
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.xml'
    )
    temp_file.write(f'<?xml version="1.0"?>{content}></testsuite>')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@when('I detect the result type from content')
def step_detect_from_content(context):
    """Detect result type from file content."""
    step_detect_result_type(context)


@given('I have a file with JSON content containing "{field1}" and "{field2}" fields')
def step_have_json_with_fields(context, field1, field2):
    """Create JSON file with specific fields."""
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.json'
    )
    temp_file.write(f'{{"{field1}": "test-1", "{field2}": "passed"}}')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@then('an UnsupportedFormatError should be raised')
def step_verify_unsupported_error(context):
    """Verify UnsupportedFormatError was raised."""
    assert context.error is not None, "Expected UnsupportedFormatError but none was raised"
    assert isinstance(context.error, UnsupportedFormatError), \
        f"Expected UnsupportedFormatError, got {type(context.error)}"


@then('the error message should list supported formats')
def step_verify_supported_formats_listed(context):
    """Verify error message lists supported formats."""
    error_msg = str(context.error)
    assert 'junit-xml' in error_msg, "Error should mention junit-xml"
    assert 'allure-json' in error_msg, "Error should mention allure-json"


@when('I request the list of supported types')
def step_request_supported_types(context):
    """Request list of supported types."""
    context.supported_types = context.factory.list_supported_types()


@then('I should receive:')
@then('I should receive')
def step_verify_supported_types(context):
    """Verify list of supported types."""
    expected_types = [row['type'] for row in context.table]
    assert set(context.supported_types) == set(expected_types), \
        f"Expected {expected_types}, got {context.supported_types}"


@given('I have a valid JUnit XML file')
def step_have_valid_junit_xml(context):
    """Create a valid JUnit XML file."""
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.xml'
    )
    temp_file.write('<?xml version="1.0"?><testsuite name="test"><testcase name="t1"/></testsuite>')
    temp_file.close()
    context.temp_files.append(temp_file.name)
    context.test_file = temp_file.name


@given('I have a directory containing Summary.html')
def step_have_extent_directory(context):
    """Create a temp directory with a Summary.html file."""
    import os
    temp_dir = tempfile.mkdtemp()
    summary_path = os.path.join(temp_dir, 'Summary.html')
    with open(summary_path, 'w') as f:
        f.write("""<!DOCTYPE html><html><head>
        <title>Test Automation Summary Report</title>
        </head><body class='extent dark'>
        <ul id='test-collection' class='test-collection'>
        <li class='test displayed active has-leaf fail' status='fail'>
        <ul class='collapsible node-list'>
        <li class='node level-1 leaf fail' status='fail'>
        <div class='collapsible-header'>
        <div class='node-name'>SampleTest</div>
        <span class='node-time'>Mar 26, 2026 06:55:58 PM</span>
        <span class='node-duration'>0h 0m 1s+0ms</span>
        </div>
        <div class='collapsible-body'><div class='node-steps'>
        <table class='bordered table-results'><tbody>
        <tr class='log' status='fail'>
        <td class='status fail'></td><td class='timestamp'>6:55:59 PM</td>
        <td class='step-details'>Sample error</td>
        </tr></tbody></table></div></div>
        </li></ul></li></ul></body></html>""")
    context.temp_files.append(temp_dir)
    context.test_file = temp_dir


@given('I have a custom parser class with format_name "{name}"')
def step_have_custom_parser_class(context, name):
    """Create a custom parser class."""
    from src.spira_integration.parser_base import TestResultParser

    class CustomTestParser(TestResultParser):
        format_name = name

        def can_parse(self, file_path):
            return False

        def parse(self, file_path):
            return []

    context.custom_parser_class = CustomTestParser


@when('I register the custom parser')
def step_register_custom_parser(context):
    """Register the custom parser."""
    context.factory.register(context.custom_parser_class)


@then('"{name}" should appear in the supported types list')
def step_verify_custom_in_list(context, name):
    """Verify custom parser appears in supported types."""
    types = context.factory.list_supported_types()
    assert name in types, f"'{name}' not in {types}"


@then('I should be able to get a parser for "{name}"')
def step_verify_can_get_custom_parser(context, name):
    """Verify we can get the custom parser."""
    parser = context.factory.get_parser(name)
    assert parser is not None


@then('each registered parser should have a can_parse method')
def step_verify_all_have_can_parse(context):
    """Verify all registered parsers have can_parse."""
    for name in context.factory.list_supported_types():
        parser = context.factory.get_parser(name)
        assert hasattr(parser, 'can_parse'), f"Parser '{name}' missing can_parse"
        assert callable(parser.can_parse), f"Parser '{name}' can_parse not callable"


@then('each registered parser should have a non-empty format_name')
def step_verify_all_have_format_name(context):
    """Verify all registered parsers have format_name."""
    for name in context.factory.list_supported_types():
        parser = context.factory.get_parser(name)
        assert getattr(parser, 'format_name', ''), f"Parser '{name}' missing format_name"
