import json
from pathlib import Path

import pandas as pd


def save_synthetic_data(
    synthetic_data: pd.DataFrame,
    output_path: str,
) -> str:
    """
    Save the synthetic dataset as a CSV file.
    """

    if not isinstance(synthetic_data, pd.DataFrame):
        raise TypeError(
            "synthetic_data must be a pandas DataFrame."
        )

    if synthetic_data.empty:
        raise ValueError(
            "Cannot save an empty synthetic dataset."
        )

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    synthetic_data.to_csv(
        path,
        index=False,
    )

    return str(path)


def save_evaluation_report(
    evaluation: dict,
    output_path: str,
) -> str:
    """
    Save the evaluation report as JSON.
    """

    if not isinstance(evaluation, dict):
        raise TypeError(
            "evaluation must be a dictionary."
        )

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            evaluation,
            file,
            indent=2,
            default=str,
        )

    return str(path)