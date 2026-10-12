import pandas as pd

from synthetic_data.pipeline import run_pipeline
from synthetic_data.config import (
    GenerationConfig,
    InputConfig,
    OutputConfig,
    PlatformConfig,
    PrivacyConfig,
    QualityConfig,
)

def test_pipeline_runs_end_to_end(tmp_path):
    input_file = tmp_path / "customers.csv"

    dataframe = pd.DataFrame(
        {
            "Customer_ID": [f"C{i:03d}" for i in range(30)],
            "Customer_Name": [
                f"Customer {i}"
                for i in range(30)
            ],
            "Phone_Number": [
                f"987654{1000 + i}"
                for i in range(30)
            ],
            "Email": [
                f"customer{i}@example.com"
                for i in range(30)
            ],
            "Age": [
                20 + (i % 30)
                for i in range(30)
            ],
            "City": (
                [
                    "Chennai",
                    "Madurai",
                    "Coimbatore",
                    "Trichy",
                    "Salem",
                ]
                * 6
            ),
            "Amount": [
                500 + (i * 137) % 5000
                for i in range(30)
            ],
        }
    )

    dataframe.to_csv(input_file, index=False)


    result = run_pipeline(
        file_path=input_file,
        row_count=20,
        config=PlatformConfig(
            generation=GenerationConfig(default_row_count=1000, ctgan_epochs=1),
            output=OutputConfig(directory=tmp_path / "output"),
            quality=QualityConfig(minimum_score=0.80),
            privacy=PrivacyConfig(fail_on_exact_match=True),
            input=InputConfig(allowed_root=tmp_path),
        ),
    )

    synthetic = result.synthetic_dataframe

    assert len(synthetic) == 20

    assert list(synthetic.columns) == list(
        dataframe.columns
    )

    assert result.profile.row_count == 30

    assert "Customer_ID" in result.detection.direct_identifiers

    assert "Customer_ID" in result.policy.protected_columns

    assert "Age" in result.policy.trainable_columns

    assert "City" in result.policy.trainable_columns

    assert "Amount" in result.policy.trainable_columns

    assert set(result.generation.dataframe.columns) == {
        "Age",
        "City",
        "Amount",
    }

    assert set(result.identifiers.generated_columns) == {
        "Customer_ID",
        "Customer_Name",
        "Phone_Number",
        "Email",
    }