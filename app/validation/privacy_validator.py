import pandas as pd


def detect_identifier_leakage(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    identifier_columns: list[str],
) -> dict:
    """
    Check whether any original identifier values appear
    in the synthetic dataset.
    """

    results = {}

    for column in identifier_columns:

        if column not in real_data.columns:
            continue

        if column not in synthetic_data.columns:
            results[column] = {
                "matches": 0,
                "leakage_detected": False,
            }
            continue

        real_values = set(
            real_data[column]
            .dropna()
            .astype(str)
        )

        synthetic_values = set(
            synthetic_data[column]
            .dropna()
            .astype(str)
        )

        matches = real_values.intersection(
            synthetic_values
        )

        results[column] = {
            "matches": len(matches),
            "matched_values": sorted(matches),
            "leakage_detected": len(matches) > 0,
        }

    return results


def detect_exact_row_leakage(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
) -> dict:
    """
    Check whether any complete synthetic row is
    identical to an original row.
    """

    common_columns = [
        column
        for column in real_data.columns
        if column in synthetic_data.columns
    ]

    if not common_columns:
        return {
            "matches": 0,
            "leakage_detected": False,
        }

    real_rows = set(
        map(
            tuple,
            real_data[common_columns]
            .astype(str)
            .to_numpy(),
        )
    )

    synthetic_rows = set(
        map(
            tuple,
            synthetic_data[common_columns]
            .astype(str)
            .to_numpy(),
        )
    )

    matches = real_rows.intersection(
        synthetic_rows
    )

    return {
        "matches": len(matches),
        "leakage_detected": len(matches) > 0,
    }


def evaluate_privacy(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    identifier_columns: list[str],
) -> dict:
    """
    Run the V0.2 privacy evaluation.
    """

    identifier_leakage = detect_identifier_leakage(
        real_data,
        synthetic_data,
        identifier_columns,
    )

    row_leakage = detect_exact_row_leakage(
        real_data,
        synthetic_data,
    )

    identifier_leakage_detected = any(
        result["leakage_detected"]
        for result in identifier_leakage.values()
    )

    overall_safe = (
        not identifier_leakage_detected
        and not row_leakage["leakage_detected"]
    )

    return {
        "safe": overall_safe,
        "identifier_leakage": identifier_leakage,
        "exact_row_leakage": row_leakage,
    }