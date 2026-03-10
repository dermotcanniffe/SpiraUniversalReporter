"""JUnit XML test result parser (minimal implementation for demo)."""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List

from ..parser_base import TestResultParser
from ..models import TestResult, TestStatus
from ..exceptions import ParseError


class JUnitParser(TestResultParser):
    """Parser for JUnit XML test results (from TestNG)."""
    
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
        
        test_results = []
        
        # Handle both <testsuites> and <testsuite> root elements
        if root.tag == 'testsuites':
            testsuites = root.findall('testsuite')
        elif root.tag == 'testsuite':
            testsuites = [root]
        else:
            raise ParseError(f"Invalid JUnit XML: root element must be 'testsuite' or 'testsuites', got '{root.tag}'")
        
        for testsuite in testsuites:
            for testcase in testsuite.findall('testcase'):
                test_result = self._parse_testcase(testcase)
                if test_result:
                    test_results.append(test_result)
        
        return test_results
    
    def _parse_testcase(self, testcase: ET.Element) -> TestResult:
        """Parse a single testcase element."""
        name = testcase.get('name', 'Unknown Test')
        classname = testcase.get('classname', '')
        if classname:
            name = f"{classname}.{name}"
        
        # Parse duration
        duration = None
        time_str = testcase.get('time')
        if time_str:
            try:
                duration = float(time_str)
            except:
                pass
        
        # Determine status
        status = TestStatus.PASSED
        error_message = None
        
        failure = testcase.find('failure')
        error = testcase.find('error')
        skipped = testcase.find('skipped')
        
        if failure is not None:
            status = TestStatus.FAILED
            error_message = failure.get('message', failure.text)
        elif error is not None:
            status = TestStatus.FAILED
            error_message = error.get('message', error.text)
        elif skipped is not None:
            status = TestStatus.SKIPPED
        
        return TestResult(
            name=name,
            status=status,
            duration=duration,
            error_message=error_message,
            evidence_files=[]
        )
