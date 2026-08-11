import pandas as pd


def profile_dataset(df: pd.DataFrame) -> dict:
    """
    Generate a basic profile of the input dataset.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Cannot profile an empty dataset.")

    column_profiles = {}

    for column in df.columns:
        column_profiles[column] = {
            "dtype": str(df[column].dtype),
            "missing_count": int(df[column].isna().sum()),
            "unique_count": int(df[column].nunique()),
        }

    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": column_profiles,
    }