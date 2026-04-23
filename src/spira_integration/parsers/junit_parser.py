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

    format_name = 'junit-xml'

    def can_parse(self, file_path: str) -> bool:
        """Detect JUnit XML — a single file or a directory containing XML files."""
        path = Path(file_path)

        if path.is_file() and path.suffix == '.xml':
            return self._is_junit_xml(path)

        if path.is_dir():
            return any(self._is_junit_xml(f) for f in path.glob('*.xml'))

        return False

    def _is_junit_xml(self, path: Path) -> bool:
        """Check if an XML file is JUnit format."""
        try:
            tree = ET.parse(str(path))
            return tree.getroot().tag in ('testsuite', 'testsuites')
        except Exception:
            return False

    def parse(self, file_path: str) -> List[TestResult]:
        """
        Parse JUnit XML test results from a file or directory.

        Args:
            file_path: Path to a JUnit XML file, or a directory containing XML files

        Returns:
            List of TestResult objects
        """
        path = Path(file_path)

        if path.is_dir():
            return self._parse_directory(path)
        elif path.is_file():
            return self._parse_file(path)
        else:
            raise ParseError(f"Path does not exist: {file_path}")

    def _parse_directory(self, directory: Path) -> List[TestResult]:
        """Parse all JUnit XML files in a directory."""
        import logging
        xml_files = sorted([
            f for f in directory.glob('*.xml')
            if self._is_junit_xml(f)
        ])

        if not xml_files:
            raise ParseError(f"No JUnit XML files found in: {directory}")

        all_results = []
        for xml_file in xml_files:
            try:
                results = self._parse_file(xml_file)
                all_results.extend(results)
            except ParseError as e:
                logging.getLogger(__name__).warning(f"Skipping {xml_file.name}: {e}")

        return all_results

    def _parse_file(self, file_path: Path) -> List[TestResult]:
        """Parse a single JUnit XML file."""
        try:
            tree = ET.parse(str(file_path))
            root = tree.getroot()
        except ET.ParseError as e:
            raise ParseError(f"Invalid XML format in {file_path.name}: {e}")
        except Exception as e:
            raise ParseError(f"Failed to read {file_path.name}: {e}")

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

        results_dir = file_path.parent
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
