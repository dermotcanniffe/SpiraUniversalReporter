"""ExtentReports HTML test result parser."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup

from ..parser_base import TestResultParser
from ..models import TestResult, TestStatus
from ..exceptions import ParseError

logger = logging.getLogger(__name__)


class ExtentParser(TestResultParser):
    """
    Parser for ExtentReports HTML output.
    
    Handles the directory-based report structure:
      Result/Report_<timestamp>/
        Summary.html              <- main entry point
        Web_TC01_<timestamp>/
          HTML Reporting/Report.html
          Screenshots/*.png
          ConsolidatedScreenshots/
        Web_TC01_<timestamp>.zip
    """

    format_name = 'extent-html'

    def can_parse(self, file_path: str) -> bool:
        """Detect ExtentReports by Summary.html presence or HTML content markers."""
        path = Path(file_path)
        if path.is_dir():
            return self._find_summary(path) is not None
        if path.is_file() and path.suffix == '.html':
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read(2000)
                return 'extent' in content.lower() and 'test-collection' in content
            except Exception:
                return False
        return False

    def parse(self, file_path: str) -> List[TestResult]:
        """
        Parse ExtentReports results from a report directory or Summary.html.
        
        Args:
            file_path: Path to Summary.html or the report directory containing it
            
        Returns:
            List of TestResult objects
        """
        path = Path(file_path)

        # Accept either the Summary.html directly or a directory containing it
        if path.is_dir():
            summary = self._find_summary(path)
        elif path.is_file() and path.name.lower() == 'summary.html':
            summary = path
        else:
            raise ParseError(
                f"Expected a directory or Summary.html, got: {file_path}"
            )

        if not summary or not summary.exists():
            raise ParseError(f"Summary.html not found in {file_path}")

        report_dir = summary.parent
        return self._parse_summary(summary, report_dir)

    def _find_summary(self, directory: Path) -> Optional[Path]:
        """Locate Summary.html, searching up to 2 levels deep."""
        # Direct child
        candidate = directory / 'Summary.html'
        if candidate.exists():
            return candidate

        # One level deeper (e.g. Result/Report_<ts>/Summary.html)
        for child in directory.iterdir():
            if child.is_dir():
                candidate = child / 'Summary.html'
                if candidate.exists():
                    return candidate
                # Two levels (Result/Report_<ts>/Summary.html)
                for grandchild in child.iterdir():
                    if grandchild.is_dir():
                        candidate = grandchild / 'Summary.html'
                        if candidate.exists():
                            return candidate
        return None

    def _parse_summary(self, summary_path: Path, report_dir: Path) -> List[TestResult]:
        """Parse the Summary.html to extract all test case results."""
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
        except Exception as e:
            raise ParseError(f"Failed to read Summary.html: {e}")

        test_results = []

        # Each leaf test case is an <li> with class 'node' and 'leaf'
        nodes = soup.select('li.node.leaf')
        if not nodes:
            # Fallback: try top-level test items
            nodes = soup.select('li.test')

        for node in nodes:
            result = self._parse_node(node, report_dir)
            if result:
                test_results.append(result)

        if not test_results:
            raise ParseError("No test results found in Summary.html")

        logger.info(f"Parsed {len(test_results)} test results from ExtentReports")
        return test_results

    def _parse_node(self, node, report_dir: Path) -> Optional[TestResult]:
        """Parse a single test node from the HTML."""
        try:
            # Test name
            name_el = node.select_one('.node-name') or node.select_one('.test-name')
            name = name_el.get_text(strip=True) if name_el else 'Unknown Test'

            # Status
            status_attr = node.get('status', '')
            status = self._map_status(status_attr)

            # Timestamps
            time_el = node.select_one('.node-time') or node.select_one('.test-time')
            start_time = self._parse_extent_time(
                time_el.get_text(strip=True) if time_el else None
            )

            # Duration
            duration_el = node.select_one('.node-duration')
            duration = self._parse_duration(
                duration_el.get_text(strip=True) if duration_el else None
            )

            end_time = None
            if start_time and duration:
                from datetime import timedelta
                end_time = start_time + timedelta(seconds=duration)

            # Error messages from step details
            error_message, stack_trace = self._extract_errors(node)

            # Evidence files (screenshots)
            evidence_files = self._find_screenshots(name, report_dir)

            # Build raw_data for TC ID extraction
            raw_data = {
                'name': name,
                'status': status_attr,
                'extent_report': True,
            }

            return TestResult(
                name=name,
                status=status,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                error_message=error_message,
                stack_trace=stack_trace,
                evidence_files=evidence_files,
                raw_data=raw_data,
            )
        except Exception as e:
            logger.warning(f"Failed to parse test node: {e}")
            return None

    def _map_status(self, extent_status: str) -> TestStatus:
        """Map ExtentReports status string to TestStatus enum."""
        status_map = {
            'pass': TestStatus.PASSED,
            'fail': TestStatus.FAILED,
            'fatal': TestStatus.FAILED,
            'error': TestStatus.FAILED,
            'warning': TestStatus.CAUTION,
            'skip': TestStatus.SKIPPED,
            'info': TestStatus.PASSED,
        }
        return status_map.get(extent_status.lower().strip(), TestStatus.BLOCKED)

    def _parse_extent_time(self, time_str: str) -> Optional[datetime]:
        """Parse ExtentReports timestamp like 'Mar 26, 2026 06:55:58 PM'."""
        if not time_str:
            return None
        try:
            return datetime.strptime(time_str, '%b %d, %Y %I:%M:%S %p')
        except ValueError:
            try:
                return datetime.strptime(time_str, '%b %d, %Y %H:%M:%S')
            except ValueError:
                logger.debug(f"Could not parse timestamp: {time_str}")
                return None

    def _parse_duration(self, duration_str: str) -> Optional[float]:
        """Parse ExtentReports duration like '0h 0m 56s+560ms'."""
        if not duration_str:
            return None
        try:
            total = 0.0
            h = re.search(r'(\d+)h', duration_str)
            m = re.search(r'(\d+)m', duration_str)
            s = re.search(r'(\d+)s', duration_str)
            ms = re.search(r'(\d+)ms', duration_str)
            if h:
                total += int(h.group(1)) * 3600
            if m:
                total += int(m.group(1)) * 60
            if s:
                total += int(s.group(1))
            if ms:
                total += int(ms.group(1)) / 1000.0
            return total if total > 0 else None
        except Exception:
            return None

    def _extract_errors(self, node) -> tuple:
        """Extract error messages from step detail rows."""
        errors = []
        rows = node.select('tr.log[status="fail"], tr.log[status="fatal"], tr.log[status="error"]')
        for row in rows:
            detail = row.select_one('td.step-details')
            if detail:
                text = detail.get_text(strip=True)
                if text:
                    errors.append(text)

        if not errors:
            return None, None

        # First error as message, all errors as stack trace
        return errors[0][:500], '\n---\n'.join(errors) if len(errors) > 1 else None

    def _find_screenshots(self, test_name: str, report_dir: Path) -> List[str]:
        """Find screenshot files for a test case in the report directory."""
        evidence = []

        # Look for directories matching the test name pattern
        # e.g. Web_TC01_26-Mar-26 06-55-56-870/Screenshots/
        for item in report_dir.iterdir():
            if item.is_dir() and item.name.startswith(test_name):
                screenshots_dir = item / 'Screenshots'
                if screenshots_dir.exists():
                    for img in sorted(screenshots_dir.iterdir()):
                        if img.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.bmp'):
                            evidence.append(str(img))

                # Also check for consolidated screenshots doc
                consolidated = item / 'ConsolidatedScreenshots'
                if consolidated.exists():
                    for doc in consolidated.iterdir():
                        if doc.suffix.lower() in ('.docx', '.pdf'):
                            evidence.append(str(doc))

        return evidence
