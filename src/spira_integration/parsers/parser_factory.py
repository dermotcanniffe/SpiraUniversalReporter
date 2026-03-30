"""Factory for creating test result parsers with plugin registry."""

import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from ..parser_base import TestResultParser
from ..exceptions import UnsupportedFormatError

logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Factory with auto-discovery and manual registration of parsers.
    
    Built-in parsers are registered automatically. Custom parsers can be
    added via register() or by placing them in a custom parsers directory.
    
    Usage:
        factory = ParserFactory()
        
        # Auto-detect format
        result_type = factory.detect_result_type('path/to/results')
        parser = factory.get_parser(result_type)
        
        # Or specify explicitly
        parser = factory.get_parser('extent-html')
        
        # Register a custom parser
        factory.register(MyCustomParser)
    """

    # Class-level registry shared across instances
    _registry: Dict[str, Type[TestResultParser]] = {}

    def __init__(self):
        """Initialize and register built-in parsers."""
        self._ensure_builtins_registered()

    @classmethod
    def register(cls, parser_class: Type[TestResultParser]) -> None:
        """
        Register a parser class.
        
        Args:
            parser_class: A TestResultParser subclass with format_name set
            
        Raises:
            ValueError: If format_name is not set or already registered
        """
        name = getattr(parser_class, 'format_name', '')
        if not name:
            raise ValueError(
                f"{parser_class.__name__} must set format_name class attribute"
            )
        if name in cls._registry:
            logger.debug(f"Overriding parser for '{name}' with {parser_class.__name__}")
        cls._registry[name] = parser_class
        logger.debug(f"Registered parser '{name}' -> {parser_class.__name__}")

    @classmethod
    def _ensure_builtins_registered(cls):
        """Register built-in parsers if not already registered."""
        if cls._registry:
            return

        from .junit_parser import JUnitParser
        from .allure_parser import AllureParser
        from .extent_parser import ExtentParser

        for parser_cls in [JUnitParser, AllureParser, ExtentParser]:
            if parser_cls.format_name and parser_cls.format_name not in cls._registry:
                cls.register(parser_cls)

    def get_parser(self, result_type: str) -> TestResultParser:
        """
        Get a parser instance for the specified result type.
        
        Args:
            result_type: Format name (e.g. 'junit-xml', 'allure-json', 'extent-html')
            
        Returns:
            TestResultParser instance
            
        Raises:
            UnsupportedFormatError: If result type is not registered
        """
        if result_type not in self._registry:
            raise UnsupportedFormatError(
                f"Unsupported result type: {result_type}. "
                f"Registered formats: {', '.join(self.list_supported_types())}"
            )
        return self._registry[result_type]()

    def detect_result_type(self, file_path: str) -> str:
        """
        Auto-detect the result type by asking each registered parser.
        
        Args:
            file_path: Path to test results file or directory
            
        Returns:
            Detected format name
            
        Raises:
            UnsupportedFormatError: If no parser can handle the input
        """
        for name, parser_cls in self._registry.items():
            try:
                instance = parser_cls()
                if instance.can_parse(file_path):
                    logger.info(f"Auto-detected format: {name}")
                    return name
            except Exception as e:
                logger.debug(f"Parser '{name}' detection failed: {e}")
                continue

        raise UnsupportedFormatError(
            f"Could not determine result type for: {file_path}. "
            f"Registered formats: {', '.join(self.list_supported_types())}"
        )

    def list_supported_types(self) -> List[str]:
        """Get list of registered format names."""
        return list(self._registry.keys())

    @classmethod
    def load_custom_parsers(cls, directory: str) -> None:
        """
        Load custom parser modules from a directory.
        
        Each .py file in the directory is imported. Any TestResultParser
        subclass with a format_name will be auto-registered.
        
        Args:
            directory: Path to directory containing custom parser .py files
        """
        parsers_dir = Path(directory)
        if not parsers_dir.is_dir():
            logger.warning(f"Custom parsers directory not found: {directory}")
            return

        for py_file in parsers_dir.glob('*.py'):
            if py_file.name.startswith('_'):
                continue
            try:
                module_name = f"custom_parsers.{py_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find and register any parser classes in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, TestResultParser)
                        and attr is not TestResultParser
                        and getattr(attr, 'format_name', '')
                    ):
                        cls.register(attr)
                        logger.info(f"Loaded custom parser: {attr.format_name} from {py_file.name}")

            except Exception as e:
                logger.warning(f"Failed to load custom parser {py_file.name}: {e}")
