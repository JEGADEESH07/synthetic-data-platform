from app.ingestion.loader import load_dataset
from app.privacy.identifier_detector import detect_identifiers
from app.privacy.data_protector import separate_identifiers


def test_identifier_detection():
    df = load_dataset("data/input/test.csv")

    identifiers = detect_identifiers(df)

    assert identifiers == [
        "Customer_ID",
        "Customer_Name",
    ]


def test_identifier_separation():
    df = load_dataset("data/input/test.csv")

    identifiers = detect_identifiers(df)

    training_data, identifier_data = (
        separate_identifiers(
            df,
            identifiers,
        )
    )

    assert list(training_data.columns) == [
        "Age",
        "City",
        "Transaction_Amount",
    ]

    assert list(identifier_data.columns) == [
        "Customer_ID",
        "Customer_Name",
    ]