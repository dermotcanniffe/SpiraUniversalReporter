"""
Test script to verify Spira API connection with real credentials.
This script loads credentials from environment variables or .env file.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from spira_integration.api.spira_client import SpiraAPIClient
from spira_integration.models import TestResult, TestStatus
from spira_integration.exceptions import AuthenticationError, APIError, ValidationError


def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        print(f"Loading environment variables from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print(f"No .env file found at {env_file}")
        print("Please create .env file from .env.example and fill in your credentials")
        return False
    return True


def test_connection():
    """Test connection to Spira API."""
    print("\n" + "="*60)
    print("SPIRA API CONNECTION TEST")
    print("="*60 + "\n")
    
    # Load credentials
    if not load_env_file():
        return False
    
    spira_url = os.getenv('SPIRA_URL')
    username = os.getenv('SPIRA_USERNAME')
    api_key = os.getenv('SPIRA_API_KEY')
    project_id = os.getenv('SPIRA_PROJECT_ID')
    
    # Validate required credentials
    missing = []
    if not spira_url:
        missing.append('SPIRA_URL')
    if not username:
        missing.append('SPIRA_USERNAME')
    if not api_key:
        missing.append('SPIRA_API_KEY')
    if not project_id:
        missing.append('SPIRA_PROJECT_ID')
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("\nPlease set these in your .env file")
        return False
    
    # Mask API key for display
    masked_key = api_key[:10] + '...' + api_key[-4:] if len(api_key) > 14 else '***'
    
    print(f"Spira URL: {spira_url}")
    print(f"Username: {username}")
    print(f"API Key: {masked_key}")
    print(f"Project ID: {project_id}")
    print()
    
    try:
        # Initialize client
        print("1. Initializing Spira API Client...")
        client = SpiraAPIClient(
            base_url=spira_url,
            username=username,
            api_key=api_key
        )
        print("   ✓ Client initialized")
        
        # Test authentication
        print("\n2. Testing authentication...")
        client.authenticate()
        print("   ✓ Authentication successful")
        
        print("\n" + "="*60)
        print("✓ CONNECTION TEST PASSED")
        print("="*60 + "\n")
        
        print("Your Spira API credentials are working correctly!")
        print("You can now use these credentials to test the integration.")
        
        return True
        
    except ValidationError as e:
        print(f"\n❌ Validation Error: {e}")
        print("\nPlease check your SPIRA_URL format")
        return False
        
    except AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("\nPlease check your username and API key")
        return False
        
    except APIError as e:
        print(f"\n❌ API Error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_test_run():
    """Test creating a test run (optional - requires test set ID and test case ID)."""
    print("\n" + "="*60)
    print("TEST RUN CREATION TEST (OPTIONAL)")
    print("="*60 + "\n")
    
    test_set_id = os.getenv('SPIRA_TEST_SET_ID')
    
    if not test_set_id:
        print("⚠ SPIRA_TEST_SET_ID not set - skipping test run creation")
        print("  To test creating test runs, add SPIRA_TEST_SET_ID to your .env file")
        return True
    
    print("⚠ Test run creation requires a valid test case ID")
    print("  This test is commented out to avoid creating unwanted test runs")
    print("  Uncomment the code below if you want to test this functionality")
    
    # Uncomment to test creating a real test run:
    # try:
    #     spira_url = os.getenv('SPIRA_URL')
    #     username = os.getenv('SPIRA_USERNAME')
    #     api_key = os.getenv('SPIRA_API_KEY')
    #     project_id = int(os.getenv('SPIRA_PROJECT_ID'))
    #     test_set_id = int(test_set_id)
    #     test_case_id = 123  # Replace with a real test case ID from your project
    #     
    #     client = SpiraAPIClient(base_url=spira_url, username=username, api_key=api_key)
    #     client.authenticate()
    #     
    #     # Create a sample test result
    #     test_result = TestResult(
    #         name="API Connection Test",
    #         status=TestStatus.PASSED,
    #         start_time=datetime.now(),
    #         end_time=datetime.now(),
    #         duration=1.0
    #     )
    #     
    #     print(f"\nCreating test run for test case {test_case_id}...")
    #     test_run_id = client.create_test_run(
    #         project_id=project_id,
    #         test_set_id=test_set_id,
    #         test_case_id=test_case_id,
    #         result=test_result
    #     )
    #     
    #     print(f"✓ Test run created successfully! Test Run ID: {test_run_id}")
    #     return True
    #     
    # except Exception as e:
    #     print(f"❌ Failed to create test run: {e}")
    #     return False
    
    return True


if __name__ == '__main__':
    success = test_connection()
    
    if success:
        test_create_test_run()
    
    sys.exit(0 if success else 1)
