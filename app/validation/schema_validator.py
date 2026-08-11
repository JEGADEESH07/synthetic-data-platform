import pandas as pd


def validate_schema(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
) -> dict:
    """
    Validate basic schema consistency between
    real and synthetic datasets.
    """

    if not isinstance(real_data, pd.DataFrame):
        raise TypeError("real_data must be a pandas DataFrame.")

    if not isinstance(synthetic_data, pd.DataFrame):
        raise TypeError(
            "synthetic_data must be a pandas DataFrame."
        )

    real_columns = list(real_data.columns)
    synthetic_columns = list(synthetic_data.columns)

    missing_columns = [
        column
        for column in real_columns
        if column not in synthetic_columns
    ]

    unexpected_columns = [
        column
        for column in synthetic_columns
        if column not in real_columns
    ]

    column_order_match = (
        real_columns == synthetic_columns
    )

    return {
        "valid": (
            not missing_columns
            and not unexpected_columns
            and column_order_match
        ),
        "real_column_count": len(real_columns),
        "synthetic_column_count": len(synthetic_columns),
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "column_order_match": column_order_match,
    }