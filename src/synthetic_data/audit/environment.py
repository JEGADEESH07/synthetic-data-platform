
"""Capture non-sensitive runtime environment metadata."""

import platform
import sys
from importlib.metadata import PackageNotFoundError, version


_TRACKED_PACKAGES = (
    "sdv",
    "pandas",
    "numpy",
    "fastapi",
    "pydantic",
)


def _package_version(package_name: str) -> str | None:
    """Return an installed package version, if available."""

    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


def capture_environment() -> dict[str, object]:
    """Capture the runtime environment for execution auditing.

    Do not include environment variables, credentials, hostnames,
    usernames, or filesystem paths.
    """

    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "packages": {
            package_name: _package_version(package_name)
            for package_name in _TRACKED_PACKAGES
        },
    }
