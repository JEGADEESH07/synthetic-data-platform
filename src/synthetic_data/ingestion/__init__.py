"""Dataset ingestion package."""

from synthetic_data.ingestion.csv_loader import (
    CSVIngestionError,
    load_csv,
)

__all__ = [
    "CSVIngestionError",
    "load_csv",
]
