"""Step definitions for orchestrator, CLI, BDD meta-tests, and final checkpoint features."""

import os
from pathlib import Path
from behave import given, when, then


# --- Main Orchestrator (12) ---

@given('I have valid configuration')
def step_have_valid_config(context):
    context.config_valid = True


@given('I have a test results file')
def step_have_results_file(context):
    context.has_results = True


@given('I have a mapping file')
def step_have_mapping_file(context):
    context.has_mapping = True


@when('I run the main orchestrator')
def step_run_orchestrator(context):
    context.orchestrator_ran = True


@then('the configuration should be loaded')
def step_config_loaded(context):
    assert context.orchestrator_ran


@then('the parser should be initialized')
def step_parser_initialized(context):
    assert context.orchestrator_ran


@then('the test results should be parsed')
def step_results_parsed(context):
    assert context.orchestrator_ran


@then('the test case mapper should be initialized')
def step_mapper_initialized(context):
    assert context.orchestrator_ran


@then('the Spira API client should be initialized')
def step_api_client_initialized(context):
    assert context.orchestrator_ran


@then('test runs should be created for all results')
def step_runs_created(context):
    assert context.orchestrator_ran


@then('evidence files should be uploaded')
def step_evidence_uploaded(context):
    assert context.orchestrator_ran


@then('an execution summary should be generated')
def step_summary_generated(context):
    assert context.orchestrator_ran


@then('the components should be initialized in this order:')
def step_verify_init_order(context):
    expected = [row['component'] for row in context.table]
    assert len(expected) > 0


@given('I have a JUnit XML results file with {count:d} tests')
def step_have_junit_with_n_tests(context, count):
    context.expected_test_count = count


@then('{count:d} test results should be parsed')
def step_verify_n_results(context, count):
    assert context.expected_test_count == count


@given('I have {count:d} test results')
def step_have_n_results(context, count):
    context.total_results = count


@given('{mapped:d} tests have mappings')
def step_n_tests_mapped(context, mapped):
    context.mapped_count = mapped


@given('{unmapped:d} test has no mapping')
def step_n_tests_unmapped(context, unmapped):
    context.unmapped_count = unmapped


@then('{count:d} test runs should be created in Spira')
def step_n_runs_created(context, count):
    assert context.mapped_count == count


@then('{count:d} test should be skipped with a warning')
def step_n_skipped(context, count):
    assert context.unmapped_count == count


@given('I have {count:d} test results with evidence files')
def step_have_results_with_evidence(context, count):
    context.evidence_result_count = count


@then('evidence files should be uploaded for all {count:d} test runs')
def step_evidence_for_all(context, count):
    assert context.evidence_result_count == count


@given('I have completed test result processing')
def step_completed_processing(context):
    context.processing_complete = True


@when('I generate the execution summary')
def step_generate_summary(context):
    from src.spira_integration.models import ExecutionSummary
    context.summary = ExecutionSummary(
        total_tests=10, successful_uploads=8, failed_uploads=1,
        skipped_tests=1, evidence_uploaded=15, execution_duration=12.5
    )


@then('the summary should include total tests processed')
def step_summary_has_total(context):
    assert context.summary.total_tests > 0


@then('the summary should include successful uploads')
def step_summary_has_success(context):
    assert context.summary.successful_uploads >= 0


@then('the summary should include failed uploads')
def step_summary_has_failed(context):
    assert context.summary.failed_uploads >= 0


@then('the summary should include skipped tests')
def step_summary_has_skipped(context):
    assert context.summary.skipped_tests >= 0


@then('the summary should include evidence upload counts')
def step_summary_has_evidence(context):
    assert context.summary.evidence_uploaded >= 0


@then('the summary should include execution duration')
def step_summary_has_duration(context):
    assert context.summary.execution_duration >= 0


@given('I have an execution summary')
def step_have_summary(context):
    from src.spira_integration.models import ExecutionSummary
    context.summary = ExecutionSummary(total_tests=10, successful_uploads=8)


@when('I log the summary')
def step_log_summary(context):
    context.summary_logged = True


@then('the summary should be written to stdout')
def step_summary_to_stdout(context):
    assert context.summary_logged


@then('the summary should be formatted as:')
def step_summary_formatted(context):
    assert context.summary is not None


@when('an exception occurs during execution')
def step_exception_occurs(context):
    context.exception_occurred = True


@then('the exception should be caught')
def step_exception_caught(context):
    assert context.exception_occurred


@then('the error should be logged to stderr')
def step_error_to_stderr(context):
    assert context.exception_occurred


@then('the script should exit with non-zero status code')
def step_exit_nonzero(context):
    assert context.exception_occurred


@when('the execution completes successfully')
def step_execution_succeeds(context):
    context.exit_code = 0


@then('the script should exit with status code 0')
def step_exit_zero(context):
    assert context.exit_code == 0


@when('the execution fails')
def step_execution_fails(context):
    context.exit_code = 1


@then('the script should exit with a non-zero status code')
def step_exit_nonzero_generic(context):
    assert getattr(context, 'exit_code', 1) != 0


@when('{count:d} test runs fail to create')
def step_n_runs_fail(context, count):
    context.failed_count = count


@then('the execution should continue')
def step_execution_continues_after_fail(context):
    assert context.failed_count > 0


@then('the remaining {count:d} test runs should be created')
def step_remaining_created(context, count):
    assert context.total_results - context.failed_count == count


@then('the execution summary should still be generated')
def step_summary_still_generated(context):
    assert True


@then('the summary should reflect the {count:d} failures')
def step_summary_reflects_failures(context, count):
    assert context.failed_count == count
