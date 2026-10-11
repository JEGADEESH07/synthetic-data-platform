"""CSV dataset ingestion."""

from pathlib import Path

import pandas as pd


class CSVIngestionError(Exception):
    """Raised when a CSV dataset cannot be ingested."""


def load_csv(file_path: str | Path) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame."""
    path = Path(file_path)

    if not path.exists():
        raise CSVIngestionError(f"File does not exist: {path}")

    if not path.is_file():
        raise CSVIngestionError(f"Path is not a file: {path}")

    if path.suffix.lower() != ".csv":
        raise CSVIngestionError(f"Unsupported file type: {path.suffix}")

    try:
        dataframe = pd.read_csv(path)
    except Exception as exc:
        raise CSVIngestionError(
            f"Failed to read CSV file: {path}"
        ) from exc

    if dataframe.empty:
        raise CSVIngestionError(f"CSV file contains no rows: {path}")

    if len(dataframe.columns) == 0:
        raise CSVIngestionError(f"CSV file contains no columns: {path}")

    return dataframe
