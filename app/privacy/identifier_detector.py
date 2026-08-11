import pandas as pd


# Columns that should never be learned by the
# synthetic-data model as direct identifiers.
KNOWN_IDENTIFIER_COLUMNS = {
    "customer_id",
    "user_id",
    "name",
    "customer_name",
    "phone",
    "phone_number",
    "mobile",
    "mobile_number",
    "email",
    "email_address",
    "address",
}


def detect_identifiers(df: pd.DataFrame) -> list[str]:
    """
    Detect likely direct identifier columns using
    known identifier naming patterns.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    identifiers = []

    for column in df.columns:
        normalized_column = column.strip().lower()

        if normalized_column in KNOWN_IDENTIFIER_COLUMNS:
            identifiers.append(column)

    return identifiers
    