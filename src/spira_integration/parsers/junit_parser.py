"""JUnit XML test result parser for TestNG and standard JUnit output."""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..parser_base import TestResultParser
from ..models import TestResult, TestStatus
from ..exceptions import ParseError


class JUnitParser(TestResultParser):
    """Parser for JUnit XML test results (from TestNG and other frameworks)."""

    def parse(self, file_path: str) -> List[TestResult]:
        """
        Parse JUnit XML test results.

        Args:
            file_path: Path to JUnit XML file

        Returns:
            List of TestResult objects

        Raises:
            ParseError: If file cannot be parsed
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            raise ParseError(f"Invalid XML format: {e}")
        except Exception as e:
            raise ParseError(f"Failed to read file: {e}")

        # Handle both <testsuites> and <testsuite> root elements
        if root.tag == 'testsuites':
            testsuites = root.findall('testsuite')
        elif root.tag == 'testsuite':
            testsuites = [root]
        else:
            raise ParseError(
                f"Invalid JUnit XML: root element must be 'testsuite' or "
                f"'testsuites', got '{root.tag}'"
            )

        results_dir = Path(file_path).parent
        test_results = []

        for testsuite in testsuites:
            suite_timestamp = self._parse_iso_timestamp(
                testsuite.get('timestamp')
            )
            for testcase in testsuite.findall('testcase'):
                result = self._parse_testcase(
                    testcase, suite_timestamp, results_dir
                )
                if result:
                    test_results.append(result)

        return test_results

    def _parse_testcase(
        self,
        testcase: ET.Element,
        suite_timestamp: Optional[datetime],
        results_dir: Path,
    ) -> TestResult:
        """Parse a single testcase element."""
        name = testcase.get('name', 'Unknown Test')
        classname = testcase.get('classname', '')
        full_name = f"{classname}.{name}" if classname else name

        # Duration
        duration = None
        time_str = testcase.get('time')
        if time_str:
            try:
                duration = float(time_str)
            except ValueError:
                pass

        # Timestamps — use suite timestamp + duration if available
        start_time = suite_timestamp
        end_time = None
        if start_time and duration is not None:
            from datetime import timedelta
            end_time = start_time + timedelta(seconds=duration)

        # Status, error message, stack trace
        status = TestStatus.PASSED
        error_message = None
        stack_trace = None

        failure = testcase.find('failure')
        error = testcase.find('error')
        skipped = testcase.find('skipped')

        if failure is not None:
            status = TestStatus.FAILED
            error_message = failure.get('message')
            stack_trace = failure.text
        elif error is not None:
            status = TestStatus.FAILED
            error_message = error.get('message')
            stack_trace = error.text
        elif skipped is not None:
            status = TestStatus.SKIPPED
            error_message = skipped.get('message')

        # Evidence files from system-out / system-err
        evidence_files = self._extract_evidence(testcase, results_dir)

        # Build raw_data dict for TC ID extraction
        raw_data = {
            'name': name,
            'fullName': full_name,
            'classname': classname,
        }
        # Include properties as labels for TC ID extraction
        props = testcase.find('properties')
        if props is not None:
            raw_data['labels'] = [
                {'name': p.get('name'), 'value': p.get('value', p.text or '')}
                for p in props.findall('property')
            ]

        return TestResult(
            name=full_name,
            status=status,
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            error_message=error_message,
            stack_trace=stack_trace,
            evidence_files=evidence_files,
            raw_data=raw_data,
        )

    def _extract_evidence(
        self, testcase: ET.Element, results_dir: Path
    ) -> List[str]:
        """
        Extract evidence file paths from system-out and system-err.

        Looks for lines matching:
            EVIDENCE: path/to/file.png
            [[ATTACHMENT|path/to/file.png]]
        """
        evidence_files = []
        pattern = re.compile(
            r'(?:EVIDENCE:\s*|'
            r'\[\[ATTACHMENT\|)'
            r'(.+?)(?:\]\])?$',
            re.MULTILINE,
        )

        for tag in ('system-out', 'system-err'):
            element = testcase.find(tag)
            if element is not None and element.text:
                for match in pattern.finditer(element.text):
                    path_str = match.group(1).strip()
                    evidence_path = results_dir / path_str
                    evidence_files.append(str(evidence_path))

        return evidence_files

    def _parse_iso_timestamp(self, value: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 timestamp from testsuite/testsuites attributes."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            # Try common JUnit format: 2021-04-02T15:48:23
            try:
                return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            except (ValueError, TypeError):
                return None
