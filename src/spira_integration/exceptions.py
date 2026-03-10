"""Custom exceptions for the Spira integration tool."""


class SpiraIntegrationError(Exception):
    """Base exception for Spira integration errors."""
    pass


class ConfigurationError(SpiraIntegrationError):
    """Raised when configuration is invalid or missing."""
    pass


class ParseError(SpiraIntegrationError):
    """Raised when test result parsing fails."""
    pass


class UnsupportedFormatError(SpiraIntegrationError):
    """Raised when test result format is not supported."""
    pass


class AuthenticationError(SpiraIntegrationError):
    """Raised when Spira authentication fails."""
    pass


class APIError(SpiraIntegrationError):
    """Raised when Spira API request fails."""
    pass


class RateLimitError(APIError):
    """Raised when Spira API rate limit is exceeded."""
    pass


class ValidationError(SpiraIntegrationError):
    """Raised when validation fails."""
    pass
