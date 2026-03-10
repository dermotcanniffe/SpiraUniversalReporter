"""Spira API Client for communicating with Spira REST API."""

import base64
import logging
import requests
from typing import Optional
from urllib.parse import urljoin, urlparse

from ..models import TestResult, TestStatus, SpiraTestRun
from ..exceptions import (
    AuthenticationError,
    APIError,
    ValidationError,
    RateLimitError
)


logger = logging.getLogger(__name__)


class SpiraAPIClient:
    """Client for interacting with Spira REST API v7."""
    
    def __init__(self, base_url: str, username: str, api_key: str):
        """
        Initialize Spira API Client.
        
        Args:
            base_url: Spira instance URL (e.g., https://company.spiraservice.net)
            username: Spira username
            api_key: Spira API key (with curly braces)
        
        Raises:
            ValidationError: If base_url format is invalid
        """
        self.base_url = self._validate_and_normalize_url(base_url)
        self.username = username
        self.api_key = api_key
        self._authenticated = False
        self._session = requests.Session()
        
    def _validate_and_normalize_url(self, url: str) -> str:
        """
        Validate and normalize the Spira URL.
        
        Args:
            url: URL to validate
            
        Returns:
            Normalized URL with trailing slash
            
        Raises:
            ValidationError: If URL format is invalid
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError("Invalid URL format: missing scheme or domain")
            
            # Ensure URL ends with /
            normalized = url.rstrip('/') + '/'
            return normalized
            
        except Exception as e:
            raise ValidationError(f"Invalid URL format: {str(e)}")
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build full API URL from endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL
        """
        base = urljoin(self.base_url, 'Services/v7_0/RestService.svc/')
        return urljoin(base, endpoint.lstrip('/'))
    
    def _get_auth_params(self) -> dict:
        """Get authentication query parameters."""
        return {
            'username': self.username,
            'api-key': self.api_key
        }
    
    def authenticate(self) -> None:
        """
        Authenticate with Spira API.
        
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Test authentication with a simple GET request to projects endpoint
            # This is more reliable than /users which may require admin permissions
            url = self._build_url('projects')
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response = self._session.get(
                url,
                params=self._get_auth_params(),
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 401:
                raise AuthenticationError(
                    f"Authentication failed: Invalid credentials (HTTP {response.status_code})"
                )
            elif response.status_code == 403:
                raise AuthenticationError(
                    f"Authentication failed: Access forbidden (HTTP {response.status_code}). Check user permissions."
                )
            elif response.status_code == 400:
                raise AuthenticationError(
                    f"Authentication failed: Bad request (HTTP {response.status_code}). Check API key format."
                )
            elif response.status_code != 200:
                raise AuthenticationError(
                    f"Authentication failed: HTTP {response.status_code} - {response.text}"
                )
            
            self._authenticated = True
            logger.info("Successfully authenticated with Spira API")
            
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def create_test_run(
        self,
        project_id: int,
        test_set_id: int,
        test_case_id: int,
        result: TestResult
    ) -> int:
        """
        Create a test run in Spira.
        
        Args:
            project_id: Spira project ID
            test_set_id: Spira test set ID
            test_case_id: Spira test case ID
            result: Test result to record
            
        Returns:
            Test run ID
            
        Raises:
            APIError: If API request fails
            RateLimitError: If rate limit is exceeded
        """
        if not self._authenticated:
            self.authenticate()
        
        endpoint = f'projects/{project_id}/test-runs/record'
        url = self._build_url(endpoint)
        
        # Map TestStatus to Spira execution status ID
        status_map = {
            TestStatus.PASSED: 2,  # Passed
            TestStatus.FAILED: 1,  # Failed
            TestStatus.BLOCKED: 5,  # Blocked
            TestStatus.CAUTION: 4,  # Caution
            TestStatus.SKIPPED: 6   # Not Run
        }
        
        execution_status_id = status_map.get(result.status, 3)  # Default to N/A
        
        # Build request payload
        payload = {
            "TestRunFormatId": 2,  # Automated test run
            "RunnerAssertCount": 0,
            "StartDate": result.start_time.isoformat() if result.start_time else None,
            "EndDate": result.end_time.isoformat() if result.end_time else None,
            "RunnerName": "CI/CD Integration Script",
            "RunnerTestName": result.name,
            "RunnerMessage": result.error_message or "Test completed",
            "RunnerStackTrace": result.stack_trace or "",
            "TestCaseId": test_case_id,
            "TestSetId": test_set_id,
            "ExecutionStatusId": execution_status_id
        }
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            response = self._session.post(
                url,
                params=self._get_auth_params(),
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code not in (200, 201):
                raise APIError(
                    f"Failed to create test run: HTTP {response.status_code} - {response.text}"
                )
            
            # Parse response to get test run ID
            response_data = response.json()
            test_run_id = response_data.get('TestRunId')
            
            if test_run_id:
                logger.info(f"Created test run ID: {test_run_id}")
            
            return test_run_id
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to create test run: {str(e)}")
    
    def upload_evidence(
        self,
        project_id: int,
        test_run_id: int,
        file_path: str
    ) -> None:
        """
        Upload evidence file to a test run.
        
        Args:
            project_id: Spira project ID
            test_run_id: Test run ID to attach evidence to
            file_path: Path to evidence file
            
        Raises:
            APIError: If upload fails
        """
        if not self._authenticated:
            self.authenticate()
        
        import os
        from pathlib import Path
        
        # Validate file exists
        if not os.path.exists(file_path):
            logger.warning(f"Evidence file not found: {file_path}")
            return
        
        # Read file and encode to base64
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            base64_data = base64.b64encode(file_data).decode('utf-8')
            filename = Path(file_path).name
            file_size = len(file_data)
            
        except Exception as e:
            logger.error(f"Failed to read evidence file {file_path}: {e}")
            raise APIError(f"Failed to read evidence file: {str(e)}")
        
        # Upload to Spira
        endpoint = f'projects/{project_id}/documents/file'
        url = self._build_url(endpoint)
        
        payload = {
            "BinaryData": base64_data,
            "AttachedArtifacts": [
                {
                    "ArtifactId": test_run_id,
                    "ArtifactTypeId": 5  # TestRun artifact type
                }
            ],
            "FilenameOrUrl": filename,
            "Description": f"Evidence from test run {test_run_id}",
            "Size": file_size,
            "CurrentVersion": "1.0",
            "ProjectId": project_id
        }
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            response = self._session.post(
                url,
                params=self._get_auth_params(),
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code not in (200, 201):
                raise APIError(
                    f"Failed to upload evidence: HTTP {response.status_code} - {response.text}"
                )
            
            logger.info(f"Successfully uploaded evidence: {filename}")
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Failed to upload evidence: {str(e)}")
