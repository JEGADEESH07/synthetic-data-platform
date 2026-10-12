"""CSV dataset ingestion and input security validation."""

from pathlib import Path
import csv
import pandas as pd

from synthetic_data.config import InputConfig


class CSVIngestionError(Exception):
    """Raised when a CSV dataset cannot be ingested."""


def _resolve_input_path(
    file_path: str | Path,
    config: InputConfig,
) -> Path:
    """Resolve and validate an input path against the allowed root."""

    path = Path(file_path)

    if not path.exists():
        raise CSVIngestionError(
            "Input file does not exist."
        )

    if not path.is_file():
        raise CSVIngestionError(
            "Input path is not a file."
        )

    if not config.allow_symlinks and path.is_symlink():
        raise CSVIngestionError(
            "Symlink input files are not allowed."
        )

    try:
        resolved_path = path.resolve(strict=True)
        allowed_root = config.allowed_root.resolve(strict=True)
    except OSError as exc:
        raise CSVIngestionError(
            "Could not resolve input path."
        ) from exc

    try:
        resolved_path.relative_to(allowed_root)
    except ValueError as exc:
        raise CSVIngestionError(
            "Input file is outside the allowed input directory."
        ) from exc

    return resolved_path

def _validate_csv_columns(
    path: Path,
    config: InputConfig,
) -> None:
    """Validate CSV column names before pandas normalizes duplicates."""

    if not config.reject_duplicate_columns:
        return

    try:
        with path.open(
            "r",
            encoding=config.encoding,
            newline="",
        ) as file:
            reader = csv.reader(file)
            columns = next(reader)
    except UnicodeDecodeError as exc:
        raise CSVIngestionError(
            "Input file encoding is invalid."
        ) from exc
    except StopIteration as exc:
        raise CSVIngestionError(
            "CSV file contains no columns."
        ) from exc
    except csv.Error as exc:
        raise CSVIngestionError(
            "CSV file contains malformed column headers."
        ) from exc
    except OSError as exc:
        raise CSVIngestionError(
            "Could not inspect CSV columns."
        ) from exc

    if len(columns) != len(set(columns)):
        raise CSVIngestionError(
            "CSV file contains duplicate column names."
        )

def load_csv(
    file_path: str | Path,
    config: InputConfig | None = None,
) -> pd.DataFrame:
    """Load and validate a CSV file."""

    active_config = config or InputConfig()

    path = _resolve_input_path(
        file_path,
        active_config,
    )

    if path.suffix.lower() != ".csv":
        raise CSVIngestionError(
            "Unsupported input file type."
        )

    try:
        file_size_bytes = path.stat().st_size
    except OSError as exc:
        raise CSVIngestionError(
            "Could not inspect input file."
        ) from exc

    max_file_size_bytes = (
        active_config.max_file_size_mb * 1024 * 1024
    )

    if file_size_bytes > max_file_size_bytes:
        raise CSVIngestionError(
            "Input file exceeds the configured size limit."
        )

    _validate_csv_columns(
        path,
        active_config,
    )

    try:
        dataframe = pd.read_csv(
            path,
            encoding=active_config.encoding,
        )
    except UnicodeDecodeError as exc:
        raise CSVIngestionError(
            "Input file encoding is invalid."
        ) from exc
    except Exception as exc:
        raise CSVIngestionError(
            "Failed to read input CSV file."
        ) from exc

    if dataframe.empty:
        raise CSVIngestionError(
            "CSV file contains no rows."
        )

    if len(dataframe.columns) == 0:
        raise CSVIngestionError(
            "CSV file contains no columns."
        )

    if len(dataframe) > active_config.max_input_rows:
        raise CSVIngestionError(
            "CSV file exceeds the configured row limit."
        )

    return dataframe
