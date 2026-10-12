"""Fresh synthetic identifier generation."""

from dataclasses import dataclass
from uuid import uuid4

import pandas as pd
from faker import Faker

from synthetic_data.identifiers.detector import IdentifierDetection


@dataclass(frozen=True)
class IdentifierGenerationResult:
    """Result produced by the fresh identifier generator."""

    dataframe: pd.DataFrame
    generated_columns: tuple[str, ...]


def _generate_unique_values(
    generator,
    count: int,
    excluded_values: set[str] | None = None,
) -> list[str]:
    """Generate unique values that do not overlap excluded values."""

    values: list[str] = []
    seen: set[str] = set()
    excluded = excluded_values or set()

    max_attempts = max(count * 100, 1000)
    attempts = 0

    while len(values) < count:
        attempts += 1

        if attempts > max_attempts:
            raise RuntimeError(
                "Unable to generate enough unique non-overlapping "
                "identifier values"
            )

        value = str(generator())

        if value in seen or value in excluded:
            continue

        seen.add(value)
        values.append(value)

    return values


def _generate_identifier_column(
    column_name: str,
    row_count: int,
    faker: Faker,
    excluded_values: set[str] | None = None,
) -> list[str]:
    """Generate fresh values based on the identifier column name."""

    normalized = column_name.lower()

    if (
        normalized in {
            "customer_id",
            "user_id",
            "client_id",
            "account_id",
        }
        or normalized.endswith(("_id", "_identifier"))
    ):
        prefix = column_name.replace("_ID", "").replace("_id", "")

        values = [
            f"SYN_{prefix.upper()}_{index:06d}"
            for index in range(1, row_count + 1)
        ]

        excluded = excluded_values or set()

        if any(value in excluded for value in values):
            raise RuntimeError(
                f"Generated identifier values overlap source values "
                f"for column: {column_name}"
            )

        return values

    if normalized in {
        "customer_name",
        "full_name",
        "first_name",
        "last_name",
    }:
        if normalized == "first_name":
            return _generate_unique_values(
                faker.first_name,
                row_count,
                excluded_values,
            )

        if normalized == "last_name":
            return _generate_unique_values(
                faker.last_name,
                row_count,
                excluded_values,
            )

        return _generate_unique_values(
            faker.name,
            row_count,
            excluded_values,
        )

    if normalized in {
        "phone",
        "phone_number",
        "mobile",
        "mobile_number",
    }:
        return _generate_unique_values(
            faker.phone_number,
            row_count,
            excluded_values,
        )

    if normalized in {
        "email",
        "email_address",
    }:
        return _generate_unique_values(
            faker.email,
            row_count,
            excluded_values,
        )

    if normalized == "address":
        return _generate_unique_values(
            faker.address,
            row_count,
            excluded_values,
        )

    values: list[str] = []
    excluded = excluded_values or set()

    while len(values) < row_count:
        value = f"SYN_{uuid4().hex}"

        if value not in excluded:
            values.append(value)

    return values


def generate_fresh_identifiers(
    original_dataframe: pd.DataFrame,
    synthetic_dataframe: pd.DataFrame,
    detection: IdentifierDetection,
) -> IdentifierGenerationResult:
    """Restore protected columns using newly generated values."""

    if not isinstance(original_dataframe, pd.DataFrame):
        raise TypeError(
            "original_dataframe must be a pandas DataFrame"
        )

    if not isinstance(synthetic_dataframe, pd.DataFrame):
        raise TypeError(
            "synthetic_dataframe must be a pandas DataFrame"
        )

    if not detection.direct_identifiers:
        return IdentifierGenerationResult(
            dataframe=synthetic_dataframe.copy(),
            generated_columns=(),
        )

    row_count = len(synthetic_dataframe)

    if row_count == 0:
        raise ValueError(
            "synthetic_dataframe must contain at least one row"
        )

    faker = Faker("en_IN")

    result = synthetic_dataframe.copy()
    generated_columns: list[str] = []

    for column_name in detection.direct_identifiers:
        source_values = (
            original_dataframe[column_name]
            .dropna()
            .astype(str)
        )

        excluded_values = set(source_values)

        values = _generate_identifier_column(
            column_name=column_name,
            row_count=row_count,
            faker=faker,
            excluded_values=excluded_values,
        )

        result[column_name] = values
        generated_columns.append(column_name)

    original_columns = list(original_dataframe.columns)

    ordered_columns = [
        column
        for column in original_columns
        if column in result.columns
    ]

    remaining_columns = [
        column
        for column in result.columns
        if column not in ordered_columns
    ]

    result = result[
        ordered_columns + remaining_columns
    ]

    return IdentifierGenerationResult(
        dataframe=result,
        generated_columns=tuple(generated_columns),
    )