from app.ingestion.loader import load_dataset
from app.pipeline import run_pipeline
from app.validation.schema_validator import (
    validate_schema,
)


def test_schema_validation():

    real_data = load_dataset(
        "data/input/test.csv"
    )

    result = run_pipeline(
        "data/input/test.csv",
        output_rows=10,
        epochs=10,
        output_data_path=None,
        output_report_path=None,
    )

    synthetic_data = result["synthetic_data"]

    report = validate_schema(
        real_data,
        synthetic_data,
    )

    assert report["valid"] is True

    assert report["missing_columns"] == []

    assert report["unexpected_columns"] == []

    assert report["column_order_match"] is True