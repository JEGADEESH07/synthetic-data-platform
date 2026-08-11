import pandas as pd


def compare_numeric_column(
    real: pd.Series,
    synthetic: pd.Series,
) -> dict:
    """
    Compare basic statistics for a numerical column.
    """

    real_stats = {
        "mean": float(real.mean()),
        "std": float(real.std()),
        "min": float(real.min()),
        "max": float(real.max()),
    }

    synthetic_stats = {
        "mean": float(synthetic.mean()),
        "std": float(synthetic.std()),
        "min": float(synthetic.min()),
        "max": float(synthetic.max()),
    }

    return {
        "real": real_stats,
        "synthetic": synthetic_stats,
    }


def compare_categorical_column(
    real: pd.Series,
    synthetic: pd.Series,
) -> dict:
    """
    Compare value distributions for a categorical column.
    """

    real_distribution = (
        real.value_counts(normalize=True)
        .to_dict()
    )

    synthetic_distribution = (
        synthetic.value_counts(normalize=True)
        .to_dict()
    )

    return {
        "real": {
            str(key): float(value)
            for key, value in real_distribution.items()
        },
        "synthetic": {
            str(key): float(value)
            for key, value in synthetic_distribution.items()
        },
    }


def calculate_mean_similarity(
    real_mean: float,
    synthetic_mean: float,
) -> float:
    """
    Calculate similarity between two numerical means.

    Returns a value between 0 and 1.
    """

    if real_mean == 0:
        return 1.0 if synthetic_mean == 0 else 0.0

    difference = abs(real_mean - synthetic_mean)
    relative_difference = difference / abs(real_mean)

    similarity = 1.0 - relative_difference

    return float(max(0.0, min(1.0, similarity)))


def calculate_categorical_similarity(
    real: pd.Series,
    synthetic: pd.Series,
) -> float:
    """
    Compare categorical distributions using total
    variation distance.

    Returns a value between 0 and 1.
    """

    real_distribution = real.value_counts(
        normalize=True
    )

    synthetic_distribution = synthetic.value_counts(
        normalize=True
    )

    categories = set(real_distribution.index).union(
        synthetic_distribution.index
    )

    distance = 0.0

    for category in categories:
        real_probability = real_distribution.get(
            category,
            0.0,
        )

        synthetic_probability = synthetic_distribution.get(
            category,
            0.0,
        )

        distance += abs(
            real_probability - synthetic_probability
        )

    distance *= 0.5

    similarity = 1.0 - distance

    return float(max(0.0, min(1.0, similarity)))


def evaluate_statistical_quality(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    identifier_columns: list[str] | None = None,
) -> dict:
    """
    Compare statistical characteristics between
    real and synthetic datasets.

    Identifier columns are excluded because they are
    intentionally regenerated independently.
    """

    if not isinstance(real_data, pd.DataFrame):
        raise TypeError(
            "real_data must be a pandas DataFrame."
        )

    if not isinstance(synthetic_data, pd.DataFrame):
        raise TypeError(
            "synthetic_data must be a pandas DataFrame."
        )

    if identifier_columns is None:
        identifier_columns = []

    results = {}

    for column in real_data.columns:

        if column in identifier_columns:
            continue

        if column not in synthetic_data.columns:
            continue

        real_column = real_data[column]
        synthetic_column = synthetic_data[column]

        if pd.api.types.is_numeric_dtype(real_column):

            comparison = compare_numeric_column(
                real_column,
                synthetic_column,
            )

            mean_similarity = calculate_mean_similarity(
                comparison["real"]["mean"],
                comparison["synthetic"]["mean"],
            )

            results[column] = {
                "type": "numerical",
                "comparison": comparison,
                "mean_similarity": mean_similarity,
            }

        else:

            comparison = compare_categorical_column(
                real_column,
                synthetic_column,
            )

            categorical_similarity = (
                calculate_categorical_similarity(
                    real_column,
                    synthetic_column,
                )
            )

            results[column] = {
                "type": "categorical",
                "comparison": comparison,
                "distribution_similarity": (
                    categorical_similarity
                ),
            }

    return results