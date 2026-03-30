"""
Sample Custom Parser — Copy and adapt this file to support a new test result format.

HOW TO CREATE A CUSTOM PARSER
=============================

1. Copy this file and rename it (e.g. robot_parser.py, nunit_parser.py)

2. Set `format_name` to a unique identifier for your format.
   This is the string users pass via --result-type or SPIRA_RESULT_TYPE.
   Convention: lowercase with hyphens (e.g. 'robot-xml', 'nunit-xml', 'cucumber-json')

3. Implement `can_parse()` to detect your format from a file path.
   This is called during auto-detection. Return True if the file/directory
   matches your format. Keep it fast — just check extensions, filenames,
   or a few bytes of content. Don't parse the whole file here.

4. Implement `parse()` to extract test results.
   Return a list of TestResult objects. Each TestResult needs at minimum:
     - name: test case name (str)
     - status: TestStatus enum (PASSED, FAILED, SKIPPED, BLOCKED, CAUTION)
   
   Optional but recommended:
     - duration: execution time in seconds (float)
     - start_time / end_time: datetime objects
     - error_message: failure reason (str)
     - stack_trace: full trace (str)
     - evidence_files: list of file paths to screenshots/logs/videos
     - raw_data: dict of original data (used for TC ID extraction)

5. Register your parser — pick ONE of these methods:

   a) Drop-in: Place your .py file in a custom parsers directory and call:
        ParserFactory.load_custom_parsers('/path/to/custom_parsers/')

   b) Manual: Import and register in your script:
        from spira_integration.parsers.parser_factory import ParserFactory
        from my_parser import MyParser
        ParserFactory.register(MyParser)

   c) Built-in: Add your parser to the _ensure_builtins_registered() method
      in parser_factory.py (for parsers shipped with this project)

TESTING YOUR PARSER
===================

Quick test from the command line:

    python -c "
    import sys; sys.path.insert(0, 'src')
    from spira_integration.parsers.parser_factory import ParserFactory
    from my_parser import MyParser
    ParserFactory.register(MyParser)
    
    factory = ParserFactory()
    print(factory.detect_result_type('path/to/results'))
    
    parser = factory.get_parser('my-format')
    for r in parser.parse('path/to/results'):
        print(f'{r.name}: {r.status.name}')
    "
"""

from pathlib import Path
from datetime import datetime
from typing import List

from ..parser_base import TestResultParser
from ..models import TestResult, TestStatus
from ..exceptions import ParseError


class SampleCustomParser(TestResultParser):
    """
    Sample parser — replace this with your own format logic.
    
    This example parses a simple CSV format:
        test_name,status,duration_seconds
        Login Test,passed,1.5
        Checkout Test,failed,3.2
    """

    # STEP 1: Set your format name
    format_name = 'sample-csv'

    # STEP 2: Implement detection
    def can_parse(self, file_path: str) -> bool:
        """Return True if this file looks like our format."""
        path = Path(file_path)
        if not path.is_file() or path.suffix != '.csv':
            return False
        try:
            with open(path, 'r') as f:
                header = f.readline().strip().lower()
            return 'test_name' in header and 'status' in header
        except Exception:
            return False

    # STEP 3: Implement parsing
    def parse(self, file_path: str) -> List[TestResult]:
        """Parse the CSV file into TestResult objects."""
        path = Path(file_path)
        if not path.exists():
            raise ParseError(f"File not found: {file_path}")

        results = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                header = f.readline()  # skip header row
                for line_num, line in enumerate(f, start=2):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(',')
                    if len(parts) < 2:
                        continue

                    name = parts[0].strip()
                    status = self._map_status(parts[1].strip())
                    duration = float(parts[2].strip()) if len(parts) > 2 else None

                    results.append(TestResult(
                        name=name,
                        status=status,
                        duration=duration,
                        # Populate raw_data so the TC mapper can extract identifiers
                        raw_data={'name': name},
                    ))
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Failed to parse CSV: {e}")

        if not results:
            raise ParseError("No test results found in CSV file")

        return results

    def _map_status(self, status_str: str) -> TestStatus:
        """Map your format's status strings to TestStatus enum."""
        mapping = {
            'passed': TestStatus.PASSED,
            'pass': TestStatus.PASSED,
            'failed': TestStatus.FAILED,
            'fail': TestStatus.FAILED,
            'skipped': TestStatus.SKIPPED,
            'skip': TestStatus.SKIPPED,
            'blocked': TestStatus.BLOCKED,
            'error': TestStatus.FAILED,
        }
        return mapping.get(status_str.lower(), TestStatus.BLOCKED)
