# Centralized Exception Handling Architecture
class TalentScoutError(Exception):
    """Base class for all Talent Scout exceptions."""

class ConfigurationError(TalentScoutError):
    """Raised when environment variables are missing or invalid."""

class RateLimitError(TalentScoutError):
    """Raised when an external API rate limit is hit."""

class LegacyDependencyError(TalentScoutError):
    """Raised when a deprecated service (Airtable) is detected."""
