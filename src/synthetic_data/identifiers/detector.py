"""Identifier detection and protection."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class IdentifierDetection:
    """Result of identifier detection for a dataset."""

    direct_identifiers: tuple[str, ...]
    protected_columns: tuple[str, ...]
    safe_columns: tuple[str, ...]


# These are strong direct-identifier column-name patterns.
_DIRECT_IDENTIFIER_PATTERNS = (
    "customer_id",
    "user_id",
    "client_id",
    "account_id",
    "phone",
    "phone_number",
    "mobile",
    "mobile_number",
    "email",
    "email_address",
    "customer_name",
    "full_name",
    "first_name",
    "last_name",
    "address",
)


def detect_identifiers(dataframe: pd.DataFrame) -> IdentifierDetection:
    """Detect likely direct identifiers using column-name rules."""

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    if dataframe.empty:
        raise ValueError("Cannot detect identifiers in an empty dataset")

    direct_identifiers: list[str] = []

    for column in dataframe.columns:
        normalized = str(column).strip().lower()

        if normalized in _DIRECT_IDENTIFIER_PATTERNS:
            direct_identifiers.append(str(column))

    protected_columns = tuple(direct_identifiers)

    safe_columns = tuple(
        str(column)
        for column in dataframe.columns
        if str(column) not in protected_columns
    )

    return IdentifierDetection(
        direct_identifiers=tuple(direct_identifiers),
        protected_columns=protected_columns,
        safe_columns=safe_columns,
    )


def remove_identifiers(
    dataframe: pd.DataFrame,
    detection: IdentifierDetection,
) -> pd.DataFrame:
    """Return a copy of the dataset without protected identifiers."""

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")

    protected = list(detection.protected_columns)

    return dataframe.drop(columns=protected, errors="ignore").copy()
