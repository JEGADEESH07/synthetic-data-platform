from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}


def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load a CSV or Excel dataset into a pandas DataFrame.
    """

    if not isinstance(file_path, str):
        raise TypeError(
            "file_path must be a string."
        )

    file_path = file_path.strip()

    if not file_path:
        raise ValueError(
            "Dataset path cannot be empty."
        )

    path = Path(file_path)

    # --------------------------------------------------
    # File existence
    # --------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    # --------------------------------------------------
    # Path must point to a file
    # --------------------------------------------------

    if not path.is_file():
        raise ValueError(
            f"Dataset path is not a file: {file_path}"
        )

    # --------------------------------------------------
    # File type validation
    # --------------------------------------------------

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(
            sorted(SUPPORTED_EXTENSIONS)
        )

        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported types: {supported}"
        )

    # --------------------------------------------------
    # Read dataset
    # --------------------------------------------------

    try:

        if path.stat().st_size == 0:
            raise ValueError(
                "The dataset is empty."
            )

        if extension == ".csv":
            df = pd.read_csv(path)

        else:
            df = pd.read_excel(path)

    except ValueError:
        raise

    except Exception as error:

        raise RuntimeError(
            f"Failed to read dataset: {error}"
        ) from error
    # --------------------------------------------------
    # Dataset validation
    # --------------------------------------------------

    if df.empty:
        raise ValueError(
            "The dataset is empty."
        )

    if len(df.columns) == 0:
        raise ValueError(
            "The dataset contains no columns."
        )

    # --------------------------------------------------
    # Successful load
    # --------------------------------------------------

    return df