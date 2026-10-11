"""Privacy evaluation for synthetic datasets."""

from dataclasses import dataclass

import pandas as pd

from synthetic_data.identifiers import IdentifierDetection


class PrivacyEvaluationError(Exception):
    """Raised when privacy evaluation cannot be performed."""


@dataclass(frozen=True)
class IdentifierPrivacyResult:
    """Privacy result for one protected identifier column."""

    column_name: str
    source_unique_count: int
    synthetic_unique_count: int
    exact_match_count: int
    exact_match_rate: float


@dataclass(frozen=True)
class DuplicatePrivacyResult:
    """Duplicate analysis for the synthetic dataset."""

    duplicate_row_count: int
    duplicate_row_rate: float


@dataclass(frozen=True)
class PrivacyReport:
    """Complete privacy evaluation report."""

    status: str
    identifier_results: tuple[IdentifierPrivacyResult, ...]
    duplicates: DuplicatePrivacyResult

    @property
    def total_exact_matches(self) -> int:
        """Return the total number of exact identifier matches."""
        return sum(
            result.exact_match_count
            for result in self.identifier_results
        )

    @property
    def matched_columns(self) -> tuple[str, ...]:
        """Return protected columns containing exact overlaps."""
        return tuple(
            result.column_name
            for result in self.identifier_results
            if result.exact_match_count > 0
        )


def _validate_dataframes(
    source_dataframe: pd.DataFrame,
    synthetic_dataframe: pd.DataFrame,
) -> None:
    """Validate evaluator inputs."""

    if not isinstance(source_dataframe, pd.DataFrame):
        raise TypeError(
            "source_dataframe must be a pandas DataFrame"
        )

    if not isinstance(synthetic_dataframe, pd.DataFrame):
        raise TypeError(
            "synthetic_dataframe must be a pandas DataFrame"
        )

    if source_dataframe.empty:
        raise PrivacyEvaluationError(
            "Source dataset is empty"
        )

    if synthetic_dataframe.empty:
        raise PrivacyEvaluationError(
            "Synthetic dataset is empty"
        )


def _evaluate_identifier_column(
    source_dataframe: pd.DataFrame,
    synthetic_dataframe: pd.DataFrame,
    column_name: str,
) -> IdentifierPrivacyResult:
    """Evaluate exact overlap for one protected column."""

    if column_name not in source_dataframe.columns:
        raise PrivacyEvaluationError(
            f"Protected column missing from source dataset: "
            f"{column_name}"
        )

    if column_name not in synthetic_dataframe.columns:
        raise PrivacyEvaluationError(
            f"Protected column missing from synthetic dataset: "
            f"{column_name}"
        )

    source_values = set(
        source_dataframe[column_name]
        .dropna()
        .astype(str)
    )

    synthetic_values = set(
        synthetic_dataframe[column_name]
        .dropna()
        .astype(str)
    )

    exact_matches = source_values.intersection(
        synthetic_values
    )

    exact_match_count = len(exact_matches)

    if len(synthetic_values) == 0:
        exact_match_rate = 0.0
    else:
        exact_match_rate = (
            exact_match_count
            / len(synthetic_values)
        )

    return IdentifierPrivacyResult(
        column_name=column_name,
        source_unique_count=len(source_values),
        synthetic_unique_count=len(synthetic_values),
        exact_match_count=exact_match_count,
        exact_match_rate=exact_match_rate,
    )


def _evaluate_duplicates(
    synthetic_dataframe: pd.DataFrame,
) -> DuplicatePrivacyResult:
    """Evaluate duplicate rows in synthetic data."""

    duplicate_mask = synthetic_dataframe.duplicated(
        keep=False
    )

    duplicate_row_count = int(
        duplicate_mask.sum()
    )

    duplicate_row_rate = (
        duplicate_row_count
        / len(synthetic_dataframe)
    )

    return DuplicatePrivacyResult(
        duplicate_row_count=duplicate_row_count,
        duplicate_row_rate=duplicate_row_rate,
    )


def evaluate_privacy(
    source_dataframe: pd.DataFrame,
    synthetic_dataframe: pd.DataFrame,
    detection: IdentifierDetection,
) -> PrivacyReport:
    """Evaluate basic privacy risks in synthetic data."""

    _validate_dataframes(
        source_dataframe,
        synthetic_dataframe,
    )

    if not isinstance(
        detection,
        IdentifierDetection,
    ):
        raise TypeError(
            "detection must be an IdentifierDetection"
        )

    protected_columns = list(
        detection.direct_identifiers
    )

    if not protected_columns:
        raise PrivacyEvaluationError(
            "No protected identifier columns are available "
            "for privacy evaluation"
        )

    identifier_results = tuple(
        _evaluate_identifier_column(
            source_dataframe=source_dataframe,
            synthetic_dataframe=synthetic_dataframe,
            column_name=column_name,
        )
        for column_name in protected_columns
    )

    duplicates = _evaluate_duplicates(
        synthetic_dataframe
    )

    has_exact_matches = any(
        result.exact_match_count > 0
        for result in identifier_results
    )

    has_duplicates = (
        duplicates.duplicate_row_count > 0
    )

    if has_exact_matches:
        status = "FAIL"
    elif has_duplicates:
        status = "REVIEW_REQUIRED"
    else:
        status = "PASS"

    return PrivacyReport(
        status=status,
        identifier_results=identifier_results,
        duplicates=duplicates,
    )