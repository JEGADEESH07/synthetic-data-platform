from app.ingestion.loader import load_dataset


def test_load_dataset():
    df = load_dataset("data/input/test.csv")

    assert df is not None
    assert df.shape == (3, 5)

    assert list(df.columns) == [
        "Customer_ID",
        "Customer_Name",
        "Age",
        "City",
        "Transaction_Amount",
    ]