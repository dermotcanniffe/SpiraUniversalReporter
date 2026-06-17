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
        """Detect ExtentReports by Summary.html presence, HTML content markers, or file detection."""
        path = Path(file_path)
        if path.is_dir():
            return self._find_summary(path) is not None
        if path.is_file() and path.suffix == '.html':
            return self._is_extent_html(path)
        return False

    def parse(self, file_path: str) -> List[TestResult]:
        """
        Parse ExtentReports results from a report directory or HTML report file.
        
        Args:
            file_path: Path to an ExtentReports HTML file (index.html, Summary.html, etc.)
                       or a directory containing ExtentReports output
            
        Returns:
            List of TestResult objects
        """
        path = Path(file_path)

        # Accept a direct HTML file path
        if path.is_file() and path.suffix == '.html':
            if self._is_extent_html(path):
                report_dir = path.parent
                return self._parse_summary(path, report_dir)
            else:
                raise ParseError(
                    f"File does not appear to be an ExtentReports HTML file: {file_path}"
                )

        # Accept a directory — look for the ExtentReports HTML file within
        if path.is_dir():
            summary = self._find_summary(path)
        else:
            raise ParseError(f"Path does not exist or is not supported: {file_path}")

        if not summary or not summary.exists():
            raise ParseError(f"No ExtentReports HTML file (Summary.html) found in {file_path}")

        report_dir = summary.parent
        return self._parse_summary(summary, report_dir)

    def _find_summary(self, directory: Path) -> Optional[Path]:
        """Locate ExtentReports summary HTML, searching up to 2 levels deep."""
        # Look for Summary.html first (standard name)
        for name in ['Summary.html', 'summary.html', 'Report.html', 'report.html',
                     'ExtentReport.html', 'extent-report.html', 'index.html']:
            candidate = directory / name
            if candidate.exists():
                if self._is_extent_html(candidate):
                    return candidate

        # Search one level deeper
        for child in directory.iterdir():
            if child.is_dir():
                for name in ['Summary.html', 'summary.html', 'Report.html', 'report.html',
                             'ExtentReport.html', 'extent-report.html', 'index.html']:
                    candidate = child / name
                    if candidate.exists():
                        if self._is_extent_html(candidate):
                            return candidate
                # Two levels deep
                for grandchild in child.iterdir():
                    if grandchild.is_dir():
                        for name in ['Summary.html', 'summary.html', 'Report.html',
                                     'report.html', 'ExtentReport.html', 'index.html']:
                            candidate = grandchild / name
                            if candidate.exists():
                                if self._is_extent_html(candidate):
                                    return candidate

        # Last resort: find any HTML file with ExtentReports markers
        for html_file in directory.rglob('*.html'):
            if self._is_extent_html(html_file):
                return html_file

        return None

    def _is_extent_html(self, path: Path) -> bool:
        """Check if an HTML file is an ExtentReports report."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read(5000)
            content_lower = content.lower()
            
            # Check for ExtentReports markers across multiple versions:
            # v3: 'extent' + 'test-collection' or 'node-name'
            # v4/v5 (Spark): 'extent' + 'test-detail' or 'extent-' classes
            # Generic: CDN references to extent-framework
            if 'extent' not in content_lower:
                return False
            
            extent_markers = [
                'test-collection',      # v3 marker
                'node-name',            # v3 marker
                'extent-framework',     # CDN reference (any version)
                'extentreports',        # common class/reference
                'extent.css',           # v3 stylesheet
                'extent.js',            # v3 script
                'spark-style.css',      # v5 Spark stylesheet  
                'test-detail',          # v4/v5 marker
                'extent-content',       # v5 content container
                'data-activates',       # Materialize-based Extent v3/v4
            ]
            return any(marker in content_lower or marker in content for marker in extent_markers)
        except Exception:
            return False

    def _parse_summary(self, summary_path: Path, report_dir: Path) -> List[TestResult]:
        """Parse the ExtentReports HTML to extract all test case results."""
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
        except Exception as e:
            raise ParseError(f"Failed to read ExtentReports HTML: {e}")

        test_results = []

        # Strategy 1: v3 format — leaf nodes with status attribute
        nodes = soup.select('li.node.leaf')
        if not nodes:
            # Strategy 2: v3 top-level test items
            nodes = soup.select('li.test')
        if not nodes:
            # Strategy 3: v5 Spark format — test rows in table or test-detail divs
            nodes = soup.select('div.test-detail')
        if not nodes:
            # Strategy 4: v5 Spark test list items
            nodes = soup.select('li.test-item')
        if not nodes:
            # Strategy 5: Any li with a status attribute that looks like a test
            nodes = soup.select('li[status]')

        for node in nodes:
            result = self._parse_node(node, report_dir)
            if result:
                test_results.append(result)

        if not test_results:
            raise ParseError(
                f"No test results found in ExtentReports HTML: {summary_path.name}. "
                f"The HTML structure may be from an unsupported ExtentReports version. "
                f"Please provide the Summary.html or index.html from your ExtentReports output."
            )

        logger.info(f"Parsed {len(test_results)} test results from ExtentReports")
        return test_results

    def _parse_node(self, node, report_dir: Path) -> Optional[TestResult]:
        """Parse a single test node from the HTML (supports v3 and v5 formats)."""
        try:
            # Test name (try multiple selectors across versions)
            name_el = (
                node.select_one('.node-name') or
                node.select_one('.test-name') or
                node.select_one('.name') or
                node.select_one('span.test-name') or
                node.select_one('.test-detail-name')
            )
            if not name_el:
                # Try the collapsible-header > div for v3
                name_el = node.select_one('.collapsible-header .node-name')
            name = name_el.get_text(strip=True) if name_el else 'Unknown Test'

            # Status — try attribute first, then CSS class, then text content
            status_attr = node.get('status', '')
            if not status_attr:
                # Look for status in child elements
                status_el = node.select_one('.test-status') or node.select_one('[status]')
                if status_el:
                    status_attr = status_el.get('status', '') or status_el.get_text(strip=True)
            if not status_attr:
                # Try extracting from CSS classes (e.g. class="node level-1 leaf fail")
                node_classes = node.get('class', [])
                if isinstance(node_classes, str):
                    node_classes = node_classes.split()
                status_keywords = {'pass', 'fail', 'fatal', 'error', 'warning', 'skip', 'info'}
                for cls in node_classes:
                    if cls.lower() in status_keywords:
                        status_attr = cls.lower()
                        break
            status = self._map_status(status_attr)

            # Timestamps
            time_el = node.select_one('.node-time') or node.select_one('.test-time')
            start_time = self._parse_extent_time(
                time_el.get_text(strip=True) if time_el else None
            )

            # Duration
            duration_el = node.select_one('.node-duration') or node.select_one('.time-taken')
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
            'passed': TestStatus.PASSED,
            'fail': TestStatus.FAILED,
            'failed': TestStatus.FAILED,
            'fatal': TestStatus.FAILED,
            'error': TestStatus.FAILED,
            'warning': TestStatus.CAUTION,
            'skip': TestStatus.SKIPPED,
            'skipped': TestStatus.SKIPPED,
            'info': TestStatus.PASSED,
        }
        cleaned = extent_status.lower().strip()
        result = status_map.get(cleaned, TestStatus.BLOCKED)
        if result == TestStatus.BLOCKED and cleaned:
            logger.warning(f"Unrecognized ExtentReports status '{extent_status}', defaulting to BLOCKED")
        return result

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
        evidence_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.mp4', '.avi', '.webm'}

        # Look for directories matching the test name pattern
        # e.g. Web_TC01_26-Mar-26 06-55-56-870/Screenshots/
        # Match using startswith OR contains (case-insensitive)
        test_name_lower = test_name.lower()
        
        for item in report_dir.iterdir():
            if not item.is_dir():
                continue
            item_lower = item.name.lower()
            if item_lower.startswith(test_name_lower) or test_name_lower in item_lower:
                # Check for Screenshots subdirectory
                screenshots_dir = item / 'Screenshots'
                if not screenshots_dir.exists():
                    screenshots_dir = item / 'screenshots'
                if screenshots_dir.exists():
                    for img in sorted(screenshots_dir.iterdir()):
                        if img.suffix.lower() in evidence_extensions:
                            evidence.append(str(img))

                # Also check for consolidated screenshots doc
                consolidated = item / 'ConsolidatedScreenshots'
                if not consolidated.exists():
                    consolidated = item / 'consolidatedscreenshots'
                if consolidated.exists():
                    for doc in consolidated.iterdir():
                        if doc.suffix.lower() in ('.docx', '.pdf', '.png', '.jpg', '.jpeg'):
                            evidence.append(str(doc))

                # Check for any evidence files directly in the test directory
                for f in sorted(item.rglob('*')):
                    if f.is_file() and f.suffix.lower() in evidence_extensions:
                        if str(f) not in evidence:
                            evidence.append(str(f))

        return evidence
