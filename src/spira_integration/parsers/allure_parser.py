"""Allure JSON test result parser."""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from ..parser_base import TestResultParser
from ..models import TestResult, TestStatus
from ..exceptions import ParseError


class AllureParser(TestResultParser):
    """Parser for Allure JSON test results (from Cypress)."""
    
    def parse(self, file_path: str) -> List[TestResult]:
        """
        Parse Allure JSON test results.
        
        Args:
            file_path: Path to Allure JSON file
            
        Returns:
            List of TestResult objects
            
        Raises:
            ParseError: If file cannot be parsed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ParseError(f"Failed to read file: {e}")
        
        # Handle both single result and array of results
        if isinstance(data, dict):
            results = [data]
        elif isinstance(data, list):
            results = data
        else:
            raise ParseError("Allure JSON must be an object or array")
        
        test_results = []
        results_dir = Path(file_path).parent
        
        for result in results:
            test_result = self._parse_single_result(result, results_dir)
            if test_result:
                test_results.append(test_result)
        
        return test_results
    
    def _parse_single_result(self, result: dict, results_dir: Path) -> TestResult:
        """Parse a single Allure test result."""
        try:
            # Extract basic fields
            name = result.get('name', result.get('fullName', 'Unknown Test'))
            status = self._map_status(result.get('status', 'unknown'))
            
            # Extract timestamps
            start_time = self._parse_timestamp(result.get('start'))
            stop_time = self._parse_timestamp(result.get('stop'))
            
            # Calculate duration
            duration = None
            if start_time and stop_time:
                duration = (stop_time - start_time).total_seconds()
            
            # Extract error details
            error_message = None
            stack_trace = None
            status_details = result.get('statusDetails', {})
            if status_details:
                error_message = status_details.get('message')
                stack_trace = status_details.get('trace')
            
            # Extract evidence files
            evidence_files = self._extract_evidence(result, results_dir)
            
            return TestResult(
                name=name,
                status=status,
                duration=duration,
                start_time=start_time,
                end_time=stop_time,
                error_message=error_message,
                stack_trace=stack_trace,
                evidence_files=evidence_files,
                raw_data=result  # Store raw data for TC ID extraction
            )
        except Exception as e:
            raise ParseError(f"Failed to parse test result: {e}")
    
    def _map_status(self, allure_status: str) -> TestStatus:
        """Map Allure status to TestStatus enum."""
        status_map = {
            'passed': TestStatus.PASSED,
            'failed': TestStatus.FAILED,
            'broken': TestStatus.FAILED,
            'skipped': TestStatus.SKIPPED,
            'unknown': TestStatus.BLOCKED
        }
        return status_map.get(allure_status.lower(), TestStatus.BLOCKED)
    
    def _parse_timestamp(self, timestamp: int) -> datetime:
        """Parse Allure timestamp (milliseconds since epoch)."""
        if timestamp is None:
            return None
        try:
            # Allure uses milliseconds
            return datetime.fromtimestamp(timestamp / 1000.0)
        except:
            return None
    
    def _extract_evidence(self, result: dict, results_dir: Path) -> List[str]:
        """Extract evidence file paths from attachments, walking steps recursively."""
        evidence_files = []
        self._collect_attachments(result, results_dir, evidence_files)
        return evidence_files

    def _collect_attachments(
        self, node: dict, results_dir: Path, evidence_files: List[str]
    ) -> None:
        """Recursively collect attachments from a node and its steps."""
        for attachment in node.get('attachments', []):
            source = attachment.get('source')
            if source:
                evidence_path = results_dir / source
                evidence_files.append(str(evidence_path))

        for step in node.get('steps', []):
            self._collect_attachments(step, results_dir, evidence_files)
