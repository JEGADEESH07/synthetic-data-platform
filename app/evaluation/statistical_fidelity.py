from typing import Any
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from app.validation.statistical_validator import (
    evaluate_statistical_quality,
)

def calculate_numeric_distribution_similarity(
    real: pd.Series,
    synthetic: pd.Series,
    bins: int = 20,
) -> float:
    """
    Compare numerical distributions using histogram
    total variation distance.

    Returns a similarity score between 0 and 1.
    """

    if bins <= 0:
        raise ValueError(
            "bins must be greater than zero."
        )

    real_values = pd.to_numeric(
        real,
        errors="coerce",
    ).dropna()

    synthetic_values = pd.to_numeric(
        synthetic,
        errors="coerce",
    ).dropna()

    if real_values.empty or synthetic_values.empty:
        return 0.0

    minimum = min(
        real_values.min(),
        synthetic_values.min(),
    )

    maximum = max(
        real_values.max(),
        synthetic_values.max(),
    )

    if minimum == maximum:
        return 1.0

    edges = np.linspace(
        minimum,
        maximum,
        bins + 1,
    )

    real_histogram, _ = np.histogram(
        real_values,
        bins=edges,
    )

    synthetic_histogram, _ = np.histogram(
        synthetic_values,
        bins=edges,
    )

    real_distribution = (
        real_histogram / real_histogram.sum()
    )

    synthetic_distribution = (
        synthetic_histogram
        / synthetic_histogram.sum()
    )

    distance = 0.5 * (
        abs(
            real_distribution
            - synthetic_distribution
        ).sum()
    )

    similarity = 1.0 - distance

    return float(
        max(0.0, min(1.0, similarity))
    )

def calculate_correlation_similarity(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    identifier_columns: list[str] | None = None,
) -> float:
    """
    Compare Pearson correlation structure between
    real and synthetic numerical columns.

    Returns a similarity score between 0 and 1.
    """

    if identifier_columns is None:
        identifier_columns = []

    real_numeric = (
        real_data
        .drop(
            columns=identifier_columns,
            errors="ignore",
        )
        .select_dtypes(include="number")
    )

    synthetic_numeric = (
        synthetic_data
        .drop(
            columns=identifier_columns,
            errors="ignore",
        )
        .select_dtypes(include="number")
    )

    common_columns = [
        column
        for column in real_numeric.columns
        if column in synthetic_numeric.columns
    ]

    if len(common_columns) < 2:
        return 1.0

    real_correlation = (
        real_numeric[common_columns]
        .corr(method="pearson")
    )

    synthetic_correlation = (
        synthetic_numeric[common_columns]
        .corr(method="pearson")
    )

    differences = []

    for index, column_a in enumerate(common_columns):

        for column_b in common_columns[
            index + 1:
        ]:

            real_value = real_correlation.loc[
                column_a,
                column_b,
            ]

            synthetic_value = (
                synthetic_correlation.loc[
                    column_a,
                    column_b,
                ]
            )

            if pd.isna(real_value) or pd.isna(
                synthetic_value
            ):
                continue

            differences.append(
                abs(
                    real_value
                    - synthetic_value
                )
            )

    if not differences:
        return 1.0

    mean_difference = (
        sum(differences)
        / len(differences)
    )

    similarity = 1.0 - mean_difference

    return float(
        max(0.0, min(1.0, similarity))
    )

def calculate_missingness_similarity(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    identifier_columns: list[str] | None = None,
) -> float | None:
    """
    Compare missing-value rates between real and
    synthetic datasets.

    Returns a similarity score between 0 and 1.

    Returns None when neither dataset contains any
    missing values in the evaluated columns.
    """

    if identifier_columns is None:
        identifier_columns = []

    common_columns = [
        column
        for column in real_data.columns
        if (
            column in synthetic_data.columns
            and column not in identifier_columns
        )
    ]

    if not common_columns:
        return None

    real_missingness = (
        real_data[common_columns]
        .isna()
        .mean()
    )

    synthetic_missingness = (
        synthetic_data[common_columns]
        .isna()
        .mean()
    )

    differences = (
        real_missingness
        - synthetic_missingness
    ).abs()

    if differences.empty:
        return None

    if differences.sum() == 0:
        has_missing_values = (
            real_missingness.sum() > 0
            or synthetic_missingness.sum() > 0
        )

        if not has_missing_values:
            return None

    similarity = 1.0 - float(
        differences.mean()
    )

    return float(
        max(0.0, min(1.0, similarity))
    )

class StatisticalFidelityEngine:
    """
    Evaluate statistical fidelity between real and
    synthetic datasets.
    """

    def evaluate(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        identifier_columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate statistical fidelity.

        The existing V0.2 statistical validator is used
        as the underlying evidence source.
        """

        if not isinstance(real_data, pd.DataFrame):
            raise TypeError(
                "real_data must be a pandas DataFrame."
            )

        if not isinstance(
            synthetic_data,
            pd.DataFrame,
        ):
            raise TypeError(
                "synthetic_data must be a pandas DataFrame."
            )

        if identifier_columns is None:
            identifier_columns = []

        column_results = (
            evaluate_statistical_quality(
                real_data,
                synthetic_data,
                identifier_columns,
            )
        )

        numerical_scores = []
        categorical_scores = []

        for column_name, result in column_results.items():
            if result["type"] == "numerical":

                distribution_similarity = (
                    calculate_numeric_distribution_similarity(
                        real_data[column_name],
                        synthetic_data[column_name],
                    )
                )

                result["distribution_similarity"] = (
                    distribution_similarity
                )

                numerical_scores.append(
                    (
                        result["mean_similarity"]
                        + distribution_similarity
                    )
                    / 2.0
                )

            elif result["type"] == "categorical":

                categorical_scores.append(
                    result["distribution_similarity"]
                )

        numerical_score = (
            sum(numerical_scores)
            / len(numerical_scores)
            if numerical_scores
            else None
        )

        categorical_score = (
            sum(categorical_scores)
            / len(categorical_scores)
            if categorical_scores
            else None
        )

        available_scores = [
            score
            for score in (
                numerical_score,
                categorical_score,
            )
            if score is not None
        ]
        correlation_score = calculate_correlation_similarity(
            real_data=real_data,
            synthetic_data=synthetic_data,
            identifier_columns=identifier_columns,
        )

        missingness_score = calculate_missingness_similarity(
            real_data=real_data,
            synthetic_data=synthetic_data,
            identifier_columns=identifier_columns,
        )

        overall_score = (
            sum(available_scores)
            / len(available_scores)
            if available_scores
            else 0.0
        )

        return {
            "overall_score": float(
                max(0.0, min(1.0, overall_score))
            ),
            "numerical_score": (
                float(numerical_score)
                if numerical_score is not None
                else None
            ),
            "categorical_score": (
                float(categorical_score)
                if categorical_score is not None
                else None
            ),
            "correlation_score": float(
                max(0.0, min(1.0, correlation_score))
            ),
            "missingness_score": (
                float(missingness_score)
                if missingness_score is not None
                else None
            ),
            "columns": column_results,
        }