class ConfigurationError(Exception):
    """Raised when there is an issue with the configuration."""
    pass

class SourceError(Exception):
    """Raised when there is an issue resolving or fetching a source."""
    pass
