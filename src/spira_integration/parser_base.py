"""Abstract base class for test result parsers."""

from abc import ABC, abstractmethod
from typing import List
from .models import TestResult


class TestResultParser(ABC):
    """Abstract base class for parsing test results."""
    
    @abstractmethod
    def parse(self, file_path: str) -> List[TestResult]:
        """
        Parse test results from a file.
        
        Args:
            file_path: Path to the test results file
            
        Returns:
            List of TestResult objects
            
        Raises:
            ParseError: If the file cannot be parsed
        """
        pass
