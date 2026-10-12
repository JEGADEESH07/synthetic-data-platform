from pathlib import Path

import pandas as pd
import pytest

from synthetic_data.config import InputConfig
from synthetic_data.ingestion import CSVIngestionError, load_csv


def _test_config(tmp_path: Path) -> InputConfig:
    """Create an ingestion configuration for isolated tests."""

    return InputConfig(
        allowed_root=tmp_path,
    )


def test_load_csv(tmp_path: Path) -> None:
    """A valid CSV should load into a DataFrame."""

    csv_file = tmp_path / "customers.csv"

    pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002"],
            "Amount": [100.50, 250.75],
        }
    ).to_csv(csv_file, index=False)

    dataframe = load_csv(
        csv_file,
        config=_test_config(tmp_path),
    )

    assert isinstance(dataframe, pd.DataFrame)
    assert dataframe.shape == (2, 2)
    assert list(dataframe.columns) == ["Customer_ID", "Amount"]


def test_missing_file_raises_error(tmp_path: Path) -> None:
    """A missing file should produce a clear ingestion error."""

    missing_file = tmp_path / "missing.csv"

    with pytest.raises(
        CSVIngestionError,
        match="does not exist",
    ):
        load_csv(
            missing_file,
            config=_test_config(tmp_path),
        )


def test_unsupported_file_type_raises_error(tmp_path: Path) -> None:
    """Unsupported file types should be rejected."""

    txt_file = tmp_path / "customers.txt"

    txt_file.write_text(
        "Customer_ID,Amount\nC001,100",
        encoding="utf-8",
    )

    with pytest.raises(
        CSVIngestionError,
        match="Unsupported input file type",
    ):
        load_csv(
            txt_file,
            config=_test_config(tmp_path),
        )


def test_empty_csv_raises_error(tmp_path: Path) -> None:
    """An empty CSV should be rejected."""

    csv_file = tmp_path / "empty.csv"

    csv_file.write_text(
        "Customer_ID,Amount\n",
        encoding="utf-8",
    )

    with pytest.raises(
        CSVIngestionError,
        match="contains no rows",
    ):
        load_csv(
            csv_file,
            config=_test_config(tmp_path),
        )

def test_file_outside_allowed_root_is_rejected(tmp_path: Path) -> None:
    """Files outside the configured input root should be rejected."""

    allowed_root = tmp_path / "input"
    outside_root = tmp_path / "outside"

    allowed_root.mkdir()
    outside_root.mkdir()

    csv_file = outside_root / "customers.csv"

    csv_file.write_text(
        "Customer_ID,Amount\nC001,100",
        encoding="utf-8",
    )

    config = InputConfig(
        allowed_root=allowed_root,
    )

    with pytest.raises(
        CSVIngestionError,
        match="outside the allowed input directory",
    ):
        load_csv(csv_file, config=config)


def test_input_row_limit_is_enforced(tmp_path: Path) -> None:
    """CSV files exceeding the configured row limit should be rejected."""

    csv_file = tmp_path / "large.csv"

    pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002", "C003"],
            "Amount": [100, 200, 300],
        }
    ).to_csv(csv_file, index=False)

    config = InputConfig(
        allowed_root=tmp_path,
        max_input_rows=2,
    )

    with pytest.raises(
        CSVIngestionError,
        match="exceeds the configured row limit",
    ):
        load_csv(csv_file, config=config)


def test_duplicate_columns_are_rejected(tmp_path: Path) -> None:
    """Duplicate CSV column names should be rejected."""

    csv_file = tmp_path / "duplicate_columns.csv"

    csv_file.write_text(
        "Customer_ID,Amount,Amount\nC001,100,200\n",
        encoding="utf-8",
    )

    config = InputConfig(
        allowed_root=tmp_path,
        reject_duplicate_columns=True,
    )

    with pytest.raises(
        CSVIngestionError,
        match="duplicate column names",
    ):
        load_csv(csv_file, config=config)


def test_duplicate_columns_can_be_allowed(tmp_path: Path) -> None:
    """Duplicate columns can be allowed when explicitly configured."""

    csv_file = tmp_path / "duplicate_columns.csv"

    csv_file.write_text(
        "Customer_ID,Amount,Amount\nC001,100,200\n",
        encoding="utf-8",
    )

    config = InputConfig(
        allowed_root=tmp_path,
        reject_duplicate_columns=False,
    )

    dataframe = load_csv(csv_file, config=config)

    assert len(dataframe) == 1


def test_file_size_limit_is_enforced(tmp_path: Path) -> None:
    """Files exceeding the configured size limit should be rejected."""

    csv_file = tmp_path / "large.csv"

    csv_file.write_text(
        "Customer_ID,Amount\nC001,100\n",
        encoding="utf-8",
    )

    config = InputConfig(
        allowed_root=tmp_path,
        max_file_size_mb=1,
    )

    csv_file.write_bytes(
        b"x" * (1024 * 1024 + 1)
    )

    with pytest.raises(
        CSVIngestionError,
        match="exceeds the configured size limit",
    ):
        load_csv(csv_file, config=config)


def test_invalid_encoding_is_rejected(tmp_path: Path) -> None:
    """Files that cannot be decoded using configured encoding should fail."""

    csv_file = tmp_path / "invalid_encoding.csv"

    csv_file.write_bytes(
        b"Customer_ID,Amount\nC001,\xff\xfe"
    )

    config = InputConfig(
        allowed_root=tmp_path,
        encoding="utf-8",
    )

    with pytest.raises(
        CSVIngestionError,
        match="encoding is invalid",
    ):
        load_csv(csv_file, config=config)


def test_symlink_input_is_rejected(tmp_path: Path) -> None:
    """Symlink inputs should be rejected when disabled."""

    target = tmp_path / "customers.csv"
    symlink = tmp_path / "linked.csv"

    target.write_text(
        "Customer_ID,Amount\nC001,100\n",
        encoding="utf-8",
    )

    try:
        symlink.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip(
            "Symlink creation is not available in this environment."
        )

    config = InputConfig(
        allowed_root=tmp_path,
        allow_symlinks=False,
    )

    with pytest.raises(
        CSVIngestionError,
        match="Symlink input files are not allowed",
    ):
        load_csv(symlink, config=config)