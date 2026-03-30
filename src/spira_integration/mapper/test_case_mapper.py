"""Test case mapper that extracts Spira test case IDs from test results."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TestCaseMapper:
    """
    Extracts Spira test case IDs from test result data.
    
    Supports multiple extraction strategies:
    1. From test name: [TC:123], TC-123, (TC:123), TC123
    2. From labels: testCaseId label
    3. From description: TC:123 pattern
    """
    
    # Regex patterns for TC ID extraction (in priority order)
    TC_PATTERNS = [
        r'\[TC[:\-]?(\d+)\]',      # [TC:123] or [TC-123] or [TC123]
        r'\(TC[:\-]?(\d+)\)',      # (TC:123) or (TC-123) or (TC123)
        r'TC[:\-](\d+)',           # TC:123 or TC-123
        r'TC(\d+)',                # TC123
    ]
    
    def __init__(self):
        """Initialize the test case mapper."""
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.TC_PATTERNS]
    
    def extract_test_case_id(self, test_result_data: dict) -> Optional[int]:
        """
        Extract test case ID from test result data.
        
        Args:
            test_result_data: Raw test result dictionary (e.g., from Allure JSON)
            
        Returns:
            Test case ID as integer, or None if not found
        """
        # Strategy 1: Check labels (Allure-specific)
        if 'labels' in test_result_data:
            for label in test_result_data['labels']:
                if label.get('name') == 'testCaseId':
                    try:
                        tc_id = int(label.get('value'))
                        logger.debug(f"Found TC ID {tc_id} in labels")
                        return tc_id
                    except (ValueError, TypeError):
                        pass
        
        # Strategy 2: Check test name
        name = test_result_data.get('name', '')
        tc_id = self._extract_from_text(name)
        if tc_id:
            logger.debug(f"Found TC ID {tc_id} in test name: {name}")
            return tc_id
        
        # Strategy 3: Check full name
        full_name = test_result_data.get('fullName', '')
        tc_id = self._extract_from_text(full_name)
        if tc_id:
            logger.debug(f"Found TC ID {tc_id} in full name: {full_name}")
            return tc_id
        
        # Strategy 4: Check description
        description = test_result_data.get('description', '')
        tc_id = self._extract_from_text(description)
        if tc_id:
            logger.debug(f"Found TC ID {tc_id} in description")
            return tc_id
        
        # No TC ID found
        logger.warning(f"No test case ID found for test: {name}")
        return None
    
    def _extract_from_text(self, text: str) -> Optional[int]:
        """
        Extract test case ID from text using regex patterns.
        
        Args:
            text: Text to search for TC ID
            
        Returns:
            Test case ID as integer, or None if not found
        """
        if not text:
            return None
        
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_automation_id(self, test_result_data: dict) -> Optional[str]:
        """
        Extract stable automation identifier for custom property matching.
        
        For Allure: uses top-level testCaseId hash (content-based, stable across runs).
        For JUnit: uses classname.name as fallback key.
        
        Args:
            test_result_data: Raw test result dictionary
            
        Returns:
            Automation identifier string, or None if not found
        """
        if not test_result_data:
            return None
        
        # Allure: top-level testCaseId field (content hash)
        test_case_id = test_result_data.get('testCaseId')
        if test_case_id and isinstance(test_case_id, str):
            logger.debug(f"Found automation ID from Allure testCaseId: {test_case_id}")
            return test_case_id
        
        # JUnit fallback: classname.name
        classname = test_result_data.get('classname', '')
        name = test_result_data.get('name', '')
        if classname and name:
            junit_key = f"{classname}.{name}"
            logger.debug(f"Using JUnit classname.name as automation ID: {junit_key}")
            return junit_key
        
        return None

    def get_test_case_id(self, test_name: str) -> Optional[int]:
        """
        Get test case ID from test name (legacy method for compatibility).
        
        Args:
            test_name: Test name string
            
        Returns:
            Test case ID as integer, or None if not found
        """
        return self._extract_from_text(test_name)
