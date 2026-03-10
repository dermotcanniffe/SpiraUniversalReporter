"""Behave environment configuration and hooks."""

import os
from pathlib import Path


def before_scenario(context, scenario):
    """Initialize context before each scenario."""
    # Initialize lists and dicts that we'll append to
    context.temp_files = []
    context.original_env = {}
    # Create a data holder for test results
    context.data = type('obj', (object,), {
        'config': None,
        'args': None,
        'error': None,
        'masked_config': None,
        'api_key': None
    })()


def after_scenario(context, scenario):
    """Clean up after each scenario."""
    # Restore environment variables
    if hasattr(context, 'original_env'):
        for var_name, original_value in context.original_env.items():
            if original_value is None:
                os.environ.pop(var_name, None)
            else:
                os.environ[var_name] = original_value
    
    # Clean up temp files
    if hasattr(context, 'temp_files'):
        for temp_file in context.temp_files:
            try:
                Path(temp_file).unlink()
            except:
                pass
