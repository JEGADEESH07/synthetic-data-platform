import pandas as pd


def separate_identifiers(
    df: pd.DataFrame,
    identifier_columns: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separate direct identifiers from the dataset.

    Returns:
        training_data: Non-identifier columns for the
                       synthetic-data model.
        identifier_data: Original identifier columns kept
                         outside the model.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Cannot process an empty dataset.")

    missing_columns = [
        column
        for column in identifier_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Identifier columns not found in dataset: "
            f"{missing_columns}"
        )

    identifier_data = df[identifier_columns].copy()

    training_columns = [
        column
        for column in df.columns
        if column not in identifier_columns
    ]

    if not training_columns:
        raise ValueError(
            "No non-identifier columns remain for training."
        )

    training_data = df[training_columns].copy()

    return training_data, identifier_data