
"""Version identifiers for execution audit records."""

from importlib.metadata import PackageNotFoundError, version


ENGINE_NAME = "V0.2 single-table synthesis engine"
ENGINE_VERSION = "0.2.0"
PLATFORM_PACKAGE = "synthetic-data-platform"


def capture_engine_version() -> dict[str, str]:
    """Return the platform and engine version identifiers."""

    try:
        platform_version = version(PLATFORM_PACKAGE)
    except PackageNotFoundError:
        platform_version = "unknown"

    return {
        "platform_version": platform_version,
        "engine_name": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
    }
