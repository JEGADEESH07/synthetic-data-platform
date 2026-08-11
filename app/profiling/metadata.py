from sdv.metadata import SingleTableMetadata

import pandas as pd


def detect_metadata(df: pd.DataFrame) -> SingleTableMetadata:
    """
    Automatically detect SDV metadata and apply
    application-level metadata corrections.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Cannot detect metadata from an empty dataset.")

    # --------------------------------------------------
    # 1. Automatic metadata detection
    # --------------------------------------------------

    metadata = SingleTableMetadata()

    metadata.detect_from_dataframe(
        data=df
    )

    # --------------------------------------------------
    # 2. Remove accidental primary-key inference
    # --------------------------------------------------

    metadata.primary_key = None

    # --------------------------------------------------
    # 3. Correct known business attributes
    # --------------------------------------------------

    if "City" in df.columns:
        metadata.update_column(
            column_name="City",
            sdtype="categorical",
            
        )

    # --------------------------------------------------
    # 4. Validate final metadata
    # --------------------------------------------------

    metadata.validate()

    return metadata