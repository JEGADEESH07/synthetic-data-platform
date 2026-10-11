from pathlib import Path

import pandas as pd
import pytest

from synthetic_data.ingestion import CSVIngestionError, load_csv


def test_load_csv(tmp_path: Path) -> None:
    """A valid CSV should load into a DataFrame."""
    csv_file = tmp_path / "customers.csv"

    pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002"],
            "Amount": [100.50, 250.75],
        }
    ).to_csv(csv_file, index=False)

    dataframe = load_csv(csv_file)

    assert isinstance(dataframe, pd.DataFrame)
    assert dataframe.shape == (2, 2)
    assert list(dataframe.columns) == ["Customer_ID", "Amount"]


def test_missing_file_raises_error(tmp_path: Path) -> None:
    """A missing file should produce a clear ingestion error."""
    missing_file = tmp_path / "missing.csv"

    with pytest.raises(CSVIngestionError, match="does not exist"):
        load_csv(missing_file)


def test_unsupported_file_type_raises_error(tmp_path: Path) -> None:
    """Unsupported file types should be rejected."""
    txt_file = tmp_path / "customers.txt"
    txt_file.write_text("Customer_ID,Amount\nC001,100")

    with pytest.raises(CSVIngestionError, match="Unsupported file type"):
        load_csv(txt_file)


def test_empty_csv_raises_error(tmp_path: Path) -> None:
    """An empty CSV should be rejected."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("Customer_ID,Amount\n")

    with pytest.raises(CSVIngestionError, match="contains no rows"):
        load_csv(csv_file)
