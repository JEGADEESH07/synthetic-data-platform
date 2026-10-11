"""Application entry point for the Synthetic Data Platform."""

from synthetic_data import __version__


def get_app_info() -> dict[str, str]:
    """Return basic application information."""
    return {
        "name": "Synthetic Data Engineering & Privacy Platform",
        "version": __version__,
    }
