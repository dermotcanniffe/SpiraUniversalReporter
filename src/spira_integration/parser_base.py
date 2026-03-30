"""Abstract base class for test result parsers."""

from abc import ABC, abstractmethod
from typing import List
from .models import TestResult


class TestResultParser(ABC):
    """
    Abstract base class for parsing test results.
    
    To create a custom parser:
    1. Subclass TestResultParser
    2. Set `format_name` to a unique identifier (e.g. 'my-custom-format')
    3. Implement `parse()` to return a list of TestResult objects
    4. Implement `can_parse()` to detect if a file/directory matches your format
    5. Register it with ParserFactory.register() or drop it in the parsers/ directory
    
    Example:
        class MyParser(TestResultParser):
            format_name = 'my-format'
            
            def can_parse(self, file_path: str) -> bool:
                return Path(file_path).suffix == '.myext'
            
            def parse(self, file_path: str) -> List[TestResult]:
                # ... parse logic ...
                return [TestResult(...)]
    """

    format_name: str = ''  # Override in subclass

    @abstractmethod
    def parse(self, file_path: str) -> List[TestResult]:
        """
        Parse test results from a file or directory.
        
        Args:
            file_path: Path to the test results file or directory
            
        Returns:
            List of TestResult objects
            
        Raises:
            ParseError: If the file cannot be parsed
        """
        pass

    def can_parse(self, file_path: str) -> bool:
        """
        Check if this parser can handle the given file/directory.
        
        Override this to implement format-specific detection logic.
        Default returns False (manual selection only).
        
        Args:
            file_path: Path to test results file or directory
            
        Returns:
            True if this parser can handle the input
        """
        return False
