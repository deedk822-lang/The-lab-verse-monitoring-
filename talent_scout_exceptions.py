# Centralized Exception Handling Architecture for Talent Scout

class TalentScoutError(Exception):
    """Base exception class for all custom errors within the Talent Scout system."""
    pass

class ConfigurationError(TalentScoutError):
    """
    Raised when the application encounters missing, invalid,
    or misconfigured environment variables or settings.
    """
    pass

class RateLimitError(TalentScoutError):
    """
    Raised when an external API (e.g., GitHub, HubSpot) returns a rate limit error (HTTP 429).
    This signals the system to potentially pause or implement backoff logic.
    """
    pass

class LegacyDependencyError(TalentScoutError):
    """
    Raised when the system detects configuration or code referencing
    a deprecated or removed service (e.g., Airtable, Proxycurl).
    """
    pass
