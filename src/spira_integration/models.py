"""Core data models for the Spira integration tool."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CAUTION = "caution"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """Represents a single test execution result."""
    name: str
    status: TestStatus
    duration: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    evidence_files: List[str] = field(default_factory=list)


@dataclass
class Configuration:
    """Holds all configuration parameters."""
    spira_url: str
    project_id: str
    test_set_id: str
    username: str
    api_key: str
    results_file: str
    result_type: Optional[str] = None
    mapping_file: Optional[str] = None


@dataclass
class TestCaseMapping:
    """Maps test names to Spira test case IDs."""
    exact_matches: dict = field(default_factory=dict)
    regex_patterns: dict = field(default_factory=dict)


@dataclass
class SpiraTestRun:
    """Represents a test run in Spira."""
    test_case_id: str
    execution_status: TestStatus
    start_timestamp: datetime
    end_timestamp: datetime
    error_message: Optional[str] = None
    test_run_id: Optional[str] = None


@dataclass
class ExecutionSummary:
    """Tracks execution statistics."""
    total_tests: int = 0
    successful_uploads: int = 0
    failed_uploads: int = 0
    skipped_tests: int = 0
    evidence_uploaded: int = 0
    execution_duration: float = 0.0
