"""Statistical quality evaluation for synthetic datasets."""

from dataclasses import dataclass

import pandas as pd

from synthetic_data.metadata import MetadataPolicy


class StatisticalEvaluationError(Exception):
    """Raised when statistical evaluation cannot be performed."""


@dataclass(frozen=True)
class ColumnQualityResult:
    """Quality result for one column."""

    column_name: str
    column_type: str
    score: float
    details: dict[str, float]


@dataclass(frozen=True)
class StatisticalQualityReport:
    """Overall statistical quality report."""

    overall_score: float
    columns: tuple[ColumnQualityResult, ...]

    @property
    def passed_columns(self) -> tuple[str, ...]:
        """Return columns meeting the quality threshold."""
        return tuple(
            result.column_name
            for result in self.columns
            if result.score >= 0.8
        )

    @property
    def failed_columns(self) -> tuple[str, ...]:
        """Return columns below the quality threshold."""
        return tuple(
            result.column_name
            for result in self.columns
            if result.score < 0.8
        )


def _clamp_score(value: float) -> float:
    """Keep quality scores between 0 and 1."""
    return max(0.0, min(1.0, value))


def _numerical_quality(
    source: pd.Series,
    synthetic: pd.Series,
) -> ColumnQualityResult:
    """Evaluate numerical distribution similarity."""

    source = pd.to_numeric(source, errors="coerce").dropna()
    synthetic = pd.to_numeric(synthetic, errors="coerce").dropna()

    if source.empty or synthetic.empty:
        raise StatisticalEvaluationError(
            "Numerical column contains no usable values"
        )

    source_mean = float(source.mean())
    synthetic_mean = float(synthetic.mean())

    source_std = float(source.std())
    synthetic_std = float(synthetic.std())

    source_median = float(source.median())
    synthetic_median = float(synthetic.median())

    source_q25 = float(source.quantile(0.25))
    synthetic_q25 = float(synthetic.quantile(0.25))

    source_q75 = float(source.quantile(0.75))
    synthetic_q75 = float(synthetic.quantile(0.75))

    mean_scale = max(abs(source_mean), 1.0)
    std_scale = max(abs(source_std), 1.0)
    median_scale = max(abs(source_median), 1.0)
    q25_scale = max(abs(source_q25), 1.0)
    q75_scale = max(abs(source_q75), 1.0)

    mean_error = abs(source_mean - synthetic_mean) / mean_scale
    std_error = abs(source_std - synthetic_std) / std_scale
    median_error = abs(source_median - synthetic_median) / median_scale
    q25_error = abs(source_q25 - synthetic_q25) / q25_scale
    q75_error = abs(source_q75 - synthetic_q75) / q75_scale

    score = _clamp_score(
        1.0
        - (
            mean_error
            + std_error
            + median_error
            + q25_error
            + q75_error
        )
        / 5.0
    )

    return ColumnQualityResult(
        column_name=source.name,
        column_type="numerical",
        score=score,
        details={
            "source_mean": source_mean,
            "synthetic_mean": synthetic_mean,
            "source_std": source_std,
            "synthetic_std": synthetic_std,
            "source_median": source_median,
            "synthetic_median": synthetic_median,
            "mean_error": mean_error,
            "std_error": std_error,
            "median_error": median_error,
            "q25_error": q25_error,
            "q75_error": q75_error,
        },
    )


def _categorical_quality(
    source: pd.Series,
    synthetic: pd.Series,
) -> ColumnQualityResult:
    """Evaluate categorical distribution similarity."""

    source_distribution = source.fillna(
        "<MISSING>"
    ).value_counts(normalize=True)

    synthetic_distribution = synthetic.fillna(
        "<MISSING>"
    ).value_counts(normalize=True)

    categories = set(source_distribution.index) | set(
        synthetic_distribution.index
    )

    total_variation_distance = 0.0

    for category in categories:
        source_probability = float(
            source_distribution.get(category, 0.0)
        )

        synthetic_probability = float(
            synthetic_distribution.get(category, 0.0)
        )

        total_variation_distance += abs(
            source_probability - synthetic_probability
        )

    total_variation_distance *= 0.5

    score = _clamp_score(
        1.0 - total_variation_distance
    )

    return ColumnQualityResult(
        column_name=source.name,
        column_type="categorical",
        score=score,
        details={
            "total_variation_distance": total_variation_distance,
        },
    )


def evaluate_statistical_quality(
    source_dataframe: pd.DataFrame,
    synthetic_dataframe: pd.DataFrame,
    policy: MetadataPolicy,
) -> StatisticalQualityReport:
    """Compare statistical characteristics of trainable columns."""

    if not isinstance(source_dataframe, pd.DataFrame):
        raise TypeError(
            "source_dataframe must be a pandas DataFrame"
        )

    if not isinstance(synthetic_dataframe, pd.DataFrame):
        raise TypeError(
            "synthetic_dataframe must be a pandas DataFrame"
        )

    if not isinstance(policy, MetadataPolicy):
        raise TypeError(
            "policy must be a MetadataPolicy"
        )

    if source_dataframe.empty:
        raise StatisticalEvaluationError(
            "Source dataset is empty"
        )

    if synthetic_dataframe.empty:
        raise StatisticalEvaluationError(
            "Synthetic dataset is empty"
        )

    trainable_columns = list(
        policy.trainable_columns
    )

    if not trainable_columns:
        raise StatisticalEvaluationError(
            "No trainable columns are available for evaluation"
        )

    missing_from_source = [
        column
        for column in trainable_columns
        if column not in source_dataframe.columns
    ]

    if missing_from_source:
        raise StatisticalEvaluationError(
            "Policy columns missing from source dataset: "
            f"{missing_from_source}"
        )

    missing_from_synthetic = [
        column
        for column in trainable_columns
        if column not in synthetic_dataframe.columns
    ]

    if missing_from_synthetic:
        raise StatisticalEvaluationError(
            "Policy columns missing from synthetic dataset: "
            f"{missing_from_synthetic}"
        )

    results: list[ColumnQualityResult] = []

    for column_name in trainable_columns:
        source_series = source_dataframe[column_name]
        synthetic_series = synthetic_dataframe[column_name]

        policy_column = next(
            column
            for column in policy.columns
            if column.name == column_name
        )

        if policy_column.column_type == "numerical":
            result = _numerical_quality(
                source_series,
                synthetic_series,
            )

        elif policy_column.column_type in {
            "categorical",
            "text",
            "boolean",
            "datetime",
        }:
            result = _categorical_quality(
                source_series,
                synthetic_series,
            )

        else:
            raise StatisticalEvaluationError(
                f"Unsupported column type: "
                f"{policy_column.column_type}"
            )

        results.append(result)

    overall_score = sum(
        result.score
        for result in results
    ) / len(results)

    return StatisticalQualityReport(
        overall_score=overall_score,
        columns=tuple(results),
    )