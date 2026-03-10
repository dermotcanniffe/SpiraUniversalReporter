"""Factory for creating test result parsers."""

import json
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

from ..parser_base import TestResultParser
from ..exceptions import UnsupportedFormatError


class ParserFactory:
    """Factory for creating appropriate test result parsers."""
    
    SUPPORTED_TYPES = ['junit-xml', 'allure-json']
    
    def __init__(self):
        """Initialize the parser factory."""
        self._parsers = {}
    
    def get_parser(self, result_type: str) -> TestResultParser:
        """
        Get a parser instance for the specified result type.
        
        Args:
            result_type: Type of test results (junit-xml, allure-json)
            
        Returns:
            TestResultParser instance
            
        Raises:
            UnsupportedFormatError: If result type is not supported
        """
        if result_type not in self.SUPPORTED_TYPES:
            raise UnsupportedFormatError(
                f"Unsupported result type: {result_type}. "
                f"Supported formats: {', '.join(self.SUPPORTED_TYPES)}"
            )
        
        # Lazy import to avoid circular dependencies
        if result_type == 'junit-xml':
            from .junit_parser import JUnitParser
            return JUnitParser()
        elif result_type == 'allure-json':
            from .allure_parser import AllureParser
            return AllureParser()
    
    def detect_result_type(self, file_path: str) -> str:
        """
        Detect the result type from file extension and content.
        
        Args:
            file_path: Path to the test results file
            
        Returns:
            Detected result type
            
        Raises:
            UnsupportedFormatError: If result type cannot be determined
        """
        path = Path(file_path)
        
        # Check file extension first
        if path.suffix == '.xml':
            # Verify it's actually JUnit XML by checking content
            if self._is_junit_xml(file_path):
                return 'junit-xml'
        elif path.suffix == '.json':
            # Check if it's Allure JSON
            if self._is_allure_json(file_path):
                return 'allure-json'
        
        raise UnsupportedFormatError(
            f"Could not determine result type for: {file_path}. "
            f"Supported formats: {', '.join(self.SUPPORTED_TYPES)}"
        )
    
    def _is_junit_xml(self, file_path: str) -> bool:
        """Check if file is JUnit XML format."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # JUnit XML has testsuite or testsuites as root
            return root.tag in ['testsuite', 'testsuites']
        except:
            return False
    
    def _is_allure_json(self, file_path: str) -> bool:
        """Check if file is Allure JSON format."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            # Allure results have uuid and status fields
            if isinstance(data, dict):
                return 'uuid' in data and 'status' in data
            elif isinstance(data, list) and len(data) > 0:
                return 'uuid' in data[0] and 'status' in data[0]
            return False
        except:
            return False
    
    def list_supported_types(self) -> list:
        """
        Get list of supported result types.
        
        Returns:
            List of supported format strings
        """
        return self.SUPPORTED_TYPES.copy()
