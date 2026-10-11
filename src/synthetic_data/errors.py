"""Application-wide exception hierarchy."""


class SyntheticDataPlatformError(Exception):
    """Base exception for expected application failures."""


class ConfigurationError(SyntheticDataPlatformError):
    """Raised when application configuration is invalid."""


class IngestionError(SyntheticDataPlatformError):
    """Raised when input data cannot be loaded."""


class ProfilingError(SyntheticDataPlatformError):
    """Raised when dataset profiling fails."""


class IdentifierError(SyntheticDataPlatformError):
    """Raised when identifier detection or generation fails."""


class MetadataError(SyntheticDataPlatformError):
    """Raised when metadata policy construction fails."""


class GenerationError(SyntheticDataPlatformError):
    """Raised when synthetic generation fails."""


class ValidationError(SyntheticDataPlatformError):
    """Raised when generated data fails validation."""


class EvaluationError(SyntheticDataPlatformError):
    """Raised when quality evaluation fails."""


class PrivacyError(SyntheticDataPlatformError):
    """Raised when privacy evaluation fails."""


class PersistenceError(SyntheticDataPlatformError):
    """Raised when artifacts cannot be persisted."""


class PipelineError(SyntheticDataPlatformError):
    """Raised when the end-to-end pipeline fails."""