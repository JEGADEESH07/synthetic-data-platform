from app.pipeline import run_pipeline


def test_pipeline():

    result = run_pipeline(
        "data/input/test.csv",
        output_rows=10,
        epochs=10,
        output_data_path=None,
        output_report_path=None,
    )

    assert "synthetic_data" in result
    assert "evaluation" in result

    assert "schema" in result["evaluation"]
    assert "statistical_quality" in result["evaluation"]
    assert "privacy" in result["evaluation"]

    assert result["synthetic_data"].shape == (
        10,
        5,
    )

    assert (
        result["evaluation"]["schema"]["valid"]
        is True
    )

    assert (
        result["evaluation"]["privacy"]["safe"]
        is True
    )