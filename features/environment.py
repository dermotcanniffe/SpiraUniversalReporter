"""Behave environment configuration and hooks."""

import os
from pathlib import Path


def _load_env_file():
    """Load .env file if it exists (for local development)."""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Don't override existing env vars (CI/CD takes precedence)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()


def before_all(context):
    """Load env file once before all tests."""
    _load_env_file()


def before_scenario(context, scenario):
    """Initialize context before each scenario."""
    context.temp_files = []
    context.original_env = {}
    context.data = type('obj', (object,), {
        'config': None,
        'args': None,
        'error': None,
        'masked_config': None,
        'api_key': None
    })()


def after_scenario(context, scenario):
    """Clean up after each scenario."""
    if hasattr(context, 'original_env'):
        for var_name, original_value in context.original_env.items():
            if original_value is None:
                os.environ.pop(var_name, None)
            else:
                os.environ[var_name] = original_value

    if hasattr(context, 'temp_files'):
        import shutil
        for temp_path in context.temp_files:
            try:
                p = Path(temp_path)
                if p.is_dir():
                    shutil.rmtree(p)
                elif p.exists():
                    p.unlink()
            except:
                pass
