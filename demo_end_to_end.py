"""
End-to-end demo: Parse Allure results and send to Spira with automatic TC ID extraction.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from spira_integration.parsers.parser_factory import ParserFactory
from spira_integration.api.spira_client import SpiraAPIClient
from spira_integration.mapper.test_case_mapper import TestCaseMapper
from spira_integration.models import ExecutionSummary
from spira_integration.exceptions import APIError


def load_env_file():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        return True
    return False


def main():
    """Run end-to-end demo."""
    print("\n" + "="*70)
    print("SPIRA INTEGRATION - END-TO-END DEMO")
    print("="*70 + "\n")
    
    # Load configuration
    if not load_env_file():
        print("❌ No .env file found. Please create one from .env.example")
        return 1
    
    spira_url = os.getenv('SPIRA_URL')
    username = os.getenv('SPIRA_USERNAME')
    api_key = os.getenv('SPIRA_API_KEY')
    project_id = int(os.getenv('SPIRA_PROJECT_ID', '1'))
    test_set_id = int(os.getenv('SPIRA_TEST_SET_ID', '1'))
    results_file = os.getenv('SPIRA_RESULTS_FILE', 'examples/sample-allure-results.json')
    
    print(f"Configuration:")
    print(f"  Spira URL: {spira_url}")
    print(f"  Project ID: {project_id}")
    print(f"  Test Set ID: {test_set_id}")
    print(f"  Results File: {results_file}")
    print()
    
    # Step 1: Parse test results
    print("Step 1: Parsing test results...")
    print("-" * 70)
    
    parser_factory = ParserFactory()
    result_type = parser_factory.detect_result_type(results_file)
    print(f"  Detected format: {result_type}")
    
    parser = parser_factory.get_parser(result_type)
    test_results = parser.parse(results_file)
    print(f"  ✓ Parsed {len(test_results)} test results\n")
    
    # Step 2: Extract test case IDs
    print("Step 2: Extracting Spira test case IDs...")
    print("-" * 70)
    
    mapper = TestCaseMapper()
    mapped_results = []
    skipped_results = []
    
    for result in test_results:
        tc_id = mapper.extract_test_case_id(result.raw_data) if result.raw_data else None
        
        if tc_id:
            mapped_results.append((result, tc_id))
            print(f"  ✓ {result.name[:50]:50} → TC:{tc_id}")
        else:
            skipped_results.append(result)
            print(f"  ⚠ {result.name[:50]:50} → No TC ID found")
    
    print(f"\n  Mapped: {len(mapped_results)}, Skipped: {len(skipped_results)}\n")
    
    if not mapped_results:
        print("❌ No test results could be mapped to Spira test cases")
        print("   Add TC IDs to your test names like: [TC:123] or TC-123")
        return 1
    
    # Step 3: Connect to Spira
    print("Step 3: Connecting to Spira...")
    print("-" * 70)
    
    try:
        client = SpiraAPIClient(
            base_url=spira_url,
            username=username,
            api_key=api_key
        )
        client.authenticate()
        print(f"  ✓ Connected to Spira\n")
    except Exception as e:
        print(f"  ❌ Failed to connect: {e}\n")
        return 1
    
    # Step 4: Send test runs to Spira
    print("Step 4: Creating test runs in Spira...")
    print("-" * 70)
    
    summary = ExecutionSummary()
    summary.total_tests = len(mapped_results)
    start_time = datetime.now()
    
    # Check if auto-create is enabled
    auto_create = os.getenv('SPIRA_AUTO_CREATE_TEST_CASES', 'true').lower() == 'true'
    if auto_create:
        print("  Auto-create test cases: ENABLED\n")
    else:
        print("  Auto-create test cases: DISABLED\n")
    
    for result, tc_id in mapped_results:
        try:
            test_run_id = client.create_test_run(
                project_id=project_id,
                test_set_id=test_set_id,
                test_case_id=tc_id,
                result=result
            )
            summary.successful_uploads += 1
            status_icon = "✓" if result.status.name == "PASSED" else "✗"
            test_run_url = f"{spira_url}/TestRun/{test_run_id}.aspx"
            print(f"  {status_icon} TC:{tc_id} → Test Run #{test_run_id} [{result.status.name}]")
            print(f"     {test_run_url}")
            
        except APIError as e:
            # Check if it's a 404 (test case doesn't exist)
            if '404' in str(e) and auto_create:
                try:
                    # Auto-create the test case
                    print(f"  ⚠ TC:{tc_id} not found, creating test case...")
                    new_tc_id = client.create_test_case(
                        project_id=project_id,
                        test_case_name=result.name,
                        description=f"Auto-created from test automation\n\nOriginal test: {result.name}"
                    )
                    print(f"  ✓ Created new test case: TC:{new_tc_id}")
                    
                    # Now create the test run with the new TC ID
                    test_run_id = client.create_test_run(
                        project_id=project_id,
                        test_set_id=test_set_id,
                        test_case_id=new_tc_id,
                        result=result
                    )
                    summary.successful_uploads += 1
                    status_icon = "✓" if result.status.name == "PASSED" else "✗"
                    test_run_url = f"{spira_url}/TestRun/{test_run_id}.aspx"
                    print(f"  {status_icon} TC:{new_tc_id} → Test Run #{test_run_id} [{result.status.name}]")
                    print(f"     {test_run_url}")
                    
                except Exception as create_error:
                    summary.failed_uploads += 1
                    print(f"  ❌ Failed to auto-create TC:{tc_id}: {str(create_error)[:50]}")
            else:
                summary.failed_uploads += 1
                print(f"  ❌ TC:{tc_id} → Failed: {str(e)[:50]}")
        except Exception as e:
            summary.failed_uploads += 1
            print(f"  ❌ TC:{tc_id} → Failed: {str(e)[:50]}")
    
    summary.skipped_tests = len(skipped_results)
    summary.execution_duration = (datetime.now() - start_time).total_seconds()
    
    # Summary
    print("\n" + "="*70)
    print("EXECUTION SUMMARY")
    print("="*70)
    print(f"Total tests processed:    {summary.total_tests}")
    print(f"Successfully uploaded:    {summary.successful_uploads}")
    print(f"Failed uploads:           {summary.failed_uploads}")
    print(f"Skipped (no TC ID):       {summary.skipped_tests}")
    print(f"Execution time:           {summary.execution_duration:.2f}s")
    print("="*70 + "\n")
    
    if summary.successful_uploads > 0:
        print(f"✓ Success! Check your Spira project:")
        print(f"  {spira_url}/TestSet/{test_set_id}.aspx")
        print()
        return 0
    else:
        print("❌ No test runs were created successfully")
        return 1


if __name__ == '__main__':
    sys.exit(main())
