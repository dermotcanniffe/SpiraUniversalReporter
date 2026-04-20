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

    format_name = 'allure-json'

    def can_parse(self, file_path: str) -> bool:
        """Detect Allure JSON — a single result file or a directory containing *-result.json files."""
        path = Path(file_path)

        # Single file
        if path.is_file() and path.suffix == '.json':
            return self._is_allure_result(path)

        # Directory containing *-result.json files
        if path.is_dir():
            return any(
                self._is_allure_result(f)
                for f in path.glob('*-result.json')
            )

        return False

    def _is_allure_result(self, path: Path) -> bool:
        """Check if a JSON file is an Allure result (has uuid + status)."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return 'uuid' in data and 'status' in data
            if isinstance(data, list) and len(data) > 0:
                return 'uuid' in data[0] and 'status' in data[0]
            return False
        except Exception:
            return False

    def parse(self, file_path: str) -> List[TestResult]:
        """
        Parse Allure JSON test results from a file or directory.

        Args:
            file_path: Path to a single Allure JSON file, or a directory
                       containing *-result.json files (standard Allure output)

        Returns:
            List of TestResult objects

        Raises:
            ParseError: If no results can be parsed
        """
        path = Path(file_path)

        if path.is_dir():
            return self._parse_directory(path)
        elif path.is_file():
            return self._parse_file(path)
        else:
            raise ParseError(f"Path does not exist: {file_path}")

    def _parse_directory(self, directory: Path) -> List[TestResult]:
        """Parse all *-result.json files in an Allure results directory."""
        result_files = sorted(directory.glob('*-result.json'))

        if not result_files:
            # Fallback: try any .json file that looks like an Allure result
            result_files = [
                f for f in sorted(directory.glob('*.json'))
                if self._is_allure_result(f)
            ]

        if not result_files:
            raise ParseError(f"No Allure result files found in: {directory}")

        all_results = []
        for result_file in result_files:
            try:
                results = self._parse_file(result_file)
                all_results.extend(results)
            except ParseError as e:
                # Log but continue — one bad file shouldn't stop the whole batch
                import logging
                logging.getLogger(__name__).warning(f"Skipping {result_file.name}: {e}")

        return all_results

    def _parse_file(self, file_path: Path) -> List[TestResult]:
        """Parse a single Allure JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON format in {file_path.name}: {e}")
        except Exception as e:
            raise ParseError(f"Failed to read {file_path.name}: {e}")
        
        if isinstance(data, dict):
            results = [data]
        elif isinstance(data, list):
            results = data
        else:
            raise ParseError(f"Allure JSON must be an object or array: {file_path.name}")
        
        test_results = []
        results_dir = file_path.parent
        
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
