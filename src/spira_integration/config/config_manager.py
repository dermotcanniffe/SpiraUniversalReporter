"""Configuration manager for loading and validating configuration."""

import argparse
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from ..models import Configuration
from ..exceptions import ConfigurationError, ValidationError


class ConfigurationManager:
    """Manages configuration loading from CLI arguments and environment variables."""
    
    ENV_PREFIX = "SPIRA_"
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._config: Optional[Configuration] = None
    
    def load_from_args(self, args: argparse.Namespace) -> Configuration:
        """
        Load configuration from parsed CLI arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Configuration object
            
        Raises:
            ConfigurationError: If required parameters are missing or invalid
        """
        # Get values with CLI args taking priority over env vars
        config_dict = {
            'spira_url': self._get_value('url', args),
            'project_id': self._get_value('project_id', args),
            'test_set_id': self._get_value('test_set_id', args),
            'username': self._get_value('username', args),
            'api_key': self._get_value('api_key', args),
            'results_file': self._get_value('results_file', args),
            'result_type': self._get_value('result_type', args, required=False),
            'mapping_file': self._get_value('mapping_file', args, required=False),
        }
        
        self._config = Configuration(**config_dict)
        return self._config
    
    def load_from_dict(self, config_dict: dict) -> Configuration:
        """
        Load configuration from a dictionary.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            Configuration object
        """
        self._config = Configuration(**config_dict)
        return self._config
    
    def _get_value(self, param: str, args: argparse.Namespace, required: bool = True) -> Optional[str]:
        """
        Get configuration value with priority: CLI args > env vars.
        
        Args:
            param: Parameter name
            args: Parsed CLI arguments
            required: Whether the parameter is required
            
        Returns:
            Configuration value
            
        Raises:
            ConfigurationError: If required parameter is missing
        """
        # Try CLI argument first
        cli_value = getattr(args, param, None)
        if cli_value is not None:
            return cli_value
        
        # Try environment variable
        env_key = f"{self.ENV_PREFIX}{param.upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value
        
        # Check if required
        if required:
            raise ConfigurationError(
                f"{param.replace('_', '-')} is required. "
                f"Provide via --{param.replace('_', '-')} or {env_key} environment variable."
            )
        
        return None
    
    def validate(self) -> None:
        """
        Validate the loaded configuration.
        
        Raises:
            ConfigurationError: If configuration is invalid
            ValidationError: If validation fails
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        
        # Validate URL format
        self._validate_url(self._config.spira_url)
        
        # Validate file paths exist
        self._validate_file_exists(self._config.results_file, "Results file")
        
        if self._config.mapping_file:
            self._validate_file_exists(self._config.mapping_file, "Mapping file")
    
    def _validate_url(self, url: str) -> None:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Raises:
            ValidationError: If URL format is invalid
        """
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValidationError(f"Invalid URL format: {url}")
            if result.scheme not in ['http', 'https']:
                raise ValidationError(f"URL must use http or https: {url}")
        except Exception as e:
            raise ValidationError(f"Invalid URL format: {url}") from e
    
    def _validate_file_exists(self, file_path: str, file_description: str) -> None:
        """
        Validate that a file exists.
        
        Args:
            file_path: Path to file
            file_description: Description for error message
            
        Raises:
            ConfigurationError: If file does not exist
        """
        path = Path(file_path)
        if not path.exists():
            raise ConfigurationError(f"{file_description} not found: {file_path}")
        if not path.is_file():
            raise ConfigurationError(f"{file_description} is not a file: {file_path}")
    
    def mask_sensitive_value(self, value: str, show_chars: int = 4) -> str:
        """
        Mask sensitive values for logging.
        
        Args:
            value: Value to mask
            show_chars: Number of characters to show at start
            
        Returns:
            Masked value
        """
        if not value or len(value) <= show_chars:
            return "*" * len(value) if value else ""
        return value[:show_chars] + "*" * (len(value) - show_chars)
    
    def get_masked_config(self) -> dict:
        """
        Get configuration with sensitive values masked.
        
        Returns:
            Dictionary with masked sensitive values
        """
        if self._config is None:
            return {}
        
        return {
            'spira_url': self._config.spira_url,
            'project_id': self._config.project_id,
            'test_set_id': self._config.test_set_id,
            'username': self._config.username,
            'api_key': self.mask_sensitive_value(self._config.api_key),
            'results_file': self._config.results_file,
            'result_type': self._config.result_type,
            'mapping_file': self._config.mapping_file,
        }
    
    @property
    def config(self) -> Configuration:
        """Get the loaded configuration."""
        if self._config is None:
            raise ConfigurationError("Configuration not loaded")
        return self._config


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for CLI.
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description='Spira CI/CD Test Integration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        '--spira-url',
        dest='url',
        help='Spira instance URL (or set SPIRA_URL env var)'
    )
    
    parser.add_argument(
        '--project-id',
        dest='project_id',
        help='Spira project identifier (or set SPIRA_PROJECT_ID env var)'
    )
    
    parser.add_argument(
        '--test-set-id',
        dest='test_set_id',
        help='Spira test set identifier (or set SPIRA_TEST_SET_ID env var)'
    )
    
    parser.add_argument(
        '--username',
        help='Spira username (or set SPIRA_USERNAME env var)'
    )
    
    parser.add_argument(
        '--api-key',
        dest='api_key',
        help='Spira API key (or set SPIRA_API_KEY env var)'
    )
    
    parser.add_argument(
        '--results-file',
        dest='results_file',
        help='Path to test results file (or set SPIRA_RESULTS_FILE env var)'
    )
    
    parser.add_argument(
        '--result-type',
        dest='result_type',
        choices=['junit-xml', 'allure-json'],
        help='Test result format type (or set SPIRA_RESULT_TYPE env var)'
    )
    
    parser.add_argument(
        '--mapping-file',
        dest='mapping_file',
        help='Path to test case mapping file (or set SPIRA_MAPPING_FILE env var)'
    )
    
    return parser
