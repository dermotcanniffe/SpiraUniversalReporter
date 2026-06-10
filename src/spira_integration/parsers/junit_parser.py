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
        """Detect JUnit XML — a single file or a directory containing XML files (recursive)."""
        path = Path(file_path)

        if path.is_file() and path.suffix == '.xml':
            return self._is_junit_xml(path)

        if path.is_dir():
            return any(self._is_junit_xml(f) for f in path.rglob('*.xml'))

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
        """Parse all JUnit XML files in a directory, recursively, with deduplication."""
        import logging
        xml_files = sorted([
            f for f in directory.rglob('*.xml')
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

        # Deduplicate: surefire/TestNG directories often contain the same test
        # in multiple XML files (e.g. TEST-TestSuite.xml wraps TEST-ClassName.xml,
        # or testng-results.xml duplicates individual TEST-*.xml files).
        # Keep the last occurrence per unique test key (classname.name) since
        # aggregate files tend to be parsed last and have the most complete data.
        return self._deduplicate_results(all_results)

    def _deduplicate_results(self, results: List[TestResult]) -> List[TestResult]:
        """
        Remove duplicate test results based on normalized key.
        
        When the same test appears in multiple XML files (common in surefire/TestNG),
        keep only the last occurrence per unique key. Uses the short class name
        (without package prefix) to handle cases where different XML files use
        different classname formats (e.g. junitreports/ may omit the package).
        """
        import logging
        seen = {}  # normalized_key -> (index, result)
        for i, result in enumerate(results):
            key = self._build_dedup_key(result)
            seen[key] = (i, result)

        deduped = [r for _, r in sorted(seen.values(), key=lambda x: x[0])]
        removed = len(results) - len(deduped)
        if removed > 0:
            logging.getLogger(__name__).info(
                f"Deduplicated {removed} duplicate test result(s) "
                f"({len(results)} -> {len(deduped)})"
            )
        return deduped

    def _build_dedup_key(self, result: TestResult) -> str:
        """
        Build a normalized deduplication key for a test result.
        
        Uses short class name (last segment only) + method name to ensure
        that the same test with different package prefixes is recognized as
        a duplicate. For example:
            'demothreearithmetictest.DemoThreeAddSubTest.demoThreeAddition'
            'DemoThreeAddSubTest.demoThreeAddition'
        Both normalize to: 'DemoThreeAddSubTest.demoThreeAddition'
        """
        if result.raw_data:
            classname = result.raw_data.get('classname', '')
            name = result.raw_data.get('name', '')
            if classname and name:
                # Use only the short class name (last segment after final dot)
                short_class = classname.rsplit('.', 1)[-1] if '.' in classname else classname
                return f"{short_class}.{name}"
        return result.name

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
        Extract evidence file paths from system-out, system-err, and adjacent directories.

        Looks for:
        1. Lines in system-out/system-err matching:
            EVIDENCE: path/to/file.png
            [[ATTACHMENT|path/to/file.png]]
        2. Screenshot/image files in sibling directories named after the test class
           (common in TestNG + screenshot capture frameworks)
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

        # Auto-discover evidence from adjacent screenshot directories
        # Common patterns: screenshots/, Screenshots/, images/, evidence/
        if not evidence_files:
            classname = testcase.get('classname', '')
            name = testcase.get('name', '')
            evidence_files.extend(
                self._discover_adjacent_evidence(results_dir, classname, name)
            )

        return evidence_files

    def _discover_adjacent_evidence(
        self, results_dir: Path, classname: str, test_name: str
    ) -> List[str]:
        """
        Discover screenshot/evidence files in adjacent directories.
        
        Searches for image/video files using multiple strategies:
        1. Named evidence directories (screenshots/, images/, evidence/) with files
           matching the test class or test name in their filename.
        2. Per-test subdirectories whose name matches the test class or method,
           collecting ALL image/video files within (handles sequentially numbered
           screenshots like '1_Element Validation.png').
        3. TestNG-style output directories (test-output/) with matching files.
        """
        evidence = []
        evidence_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.mp4', '.avi', '.webm'}
        
        # Build search terms from classname and test name
        search_terms = []
        if classname:
            # Use short class name (last segment)
            short_class = classname.rsplit('.', 1)[-1] if '.' in classname else classname
            search_terms.append(short_class.lower())
        if test_name:
            search_terms.append(test_name.lower())
        
        # Also check parent directory (results may be in target/surefire-reports)
        search_roots = [results_dir, results_dir.parent]
        
        # Track seen paths to avoid duplicates (important on case-insensitive filesystems)
        seen_paths = set()
        
        # Strategy 1: Look for per-test subdirectories whose name matches
        # the test class or method. When found, collect ALL evidence files inside.
        # This handles structures like:
        #   Web_TC01_<timestamp>/Screenshots/*.png
        #   DemoThreeAddSubTest/screenshots/*.png
        for root in search_roots:
            if not root.exists():
                continue
            for item in root.iterdir():
                if not item.is_dir():
                    continue
                dir_lower = item.name.lower()
                if any(term in dir_lower for term in search_terms if term):
                    # This directory matches the test — collect all evidence files
                    for f in sorted(item.rglob('*')):
                        if f.is_file() and f.suffix.lower() in evidence_extensions:
                            resolved = str(f.resolve())
                            if resolved not in seen_paths:
                                seen_paths.add(resolved)
                                evidence.append(str(f))
        
        if evidence:
            return evidence
        
        # Strategy 2: Common evidence directory names with filename matching
        evidence_dirs = ['screenshots', 'Screenshots', 'images', 'evidence',
                         'test-output']
        
        checked_dirs = set()
        for root in search_roots:
            if not root.exists():
                continue
            for dir_name in evidence_dirs:
                evidence_dir = root / dir_name
                if not evidence_dir.exists() or not evidence_dir.is_dir():
                    continue
                # Avoid checking the same dir twice (case-insensitive FS)
                resolved_dir = str(evidence_dir.resolve())
                if resolved_dir in checked_dirs:
                    continue
                checked_dirs.add(resolved_dir)
                
                for f in sorted(evidence_dir.rglob('*')):
                    if f.is_file() and f.suffix.lower() in evidence_extensions:
                        # Check if file or its parent directory relates to this test
                        fname_lower = f.stem.lower()
                        parent_lower = f.parent.name.lower()
                        if any(term in fname_lower or term in parent_lower
                               for term in search_terms if term):
                            resolved = str(f.resolve())
                            if resolved not in seen_paths:
                                seen_paths.add(resolved)
                                evidence.append(str(f))
        
        return evidence

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
