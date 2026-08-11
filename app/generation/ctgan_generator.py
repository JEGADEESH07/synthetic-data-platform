import pandas as pd

from sdv.metadata import SingleTableMetadata
from sdv.single_table import CTGANSynthesizer


def train_ctgan(
    df: pd.DataFrame,
    metadata: SingleTableMetadata,
    epochs: int = 300,
) -> CTGANSynthesizer:
    """
    Train CTGAN using the already validated application metadata.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if df.empty:
        raise ValueError("Cannot train CTGAN on an empty dataset.")

    if not isinstance(metadata, SingleTableMetadata):
        raise TypeError(
            "metadata must be a SingleTableMetadata object."
        )

    metadata.validate()

    synthesizer = CTGANSynthesizer(
        metadata=metadata,
        epochs=epochs,
        verbose=True,
    )

    synthesizer.fit(df)

    return synthesizer


def generate_synthetic_data(
    synthesizer: CTGANSynthesizer,
    num_rows: int,
) -> pd.DataFrame:
    """
    Generate synthetic records from a trained CTGAN model.
    """

    if num_rows <= 0:
        raise ValueError(
            "num_rows must be greater than zero."
        )

    return synthesizer.sample(
        num_rows=num_rows
    )