from pathlib import Path

import pandas as pd
import pytest

from synthetic_data.persistence import ArtifactPaths
from synthetic_data.worker.engine import EngineExecutionError, V02Engine


def test_engine_executes_v02_pipeline(monkeypatch, tmp_path):
    source = pd.DataFrame(
        {
            "Customer_ID": ["C001", "C002"],
            "Age": [25, 35],
        }
    )

    synthetic = pd.DataFrame(
        {
            "Customer_ID": ["S001", "S002"],
            "Age": [27, 33],
        }
    )

    class FakeResult:
        source_dataframe = source
        synthetic_dataframe = synthetic
        detection = object()

    artifacts = ArtifactPaths(
        job_id="job-001",
        output_directory=tmp_path / "job-001",
        synthetic_data_path=tmp_path / "job-001" / "synthetic_data.csv",
        report_path=tmp_path / "job-001" / "report.json",
    )

    monkeypatch.setattr(
        "synthetic_data.worker.engine.run_pipeline",
        lambda file_path, row_count: FakeResult(),
    )

    monkeypatch.setattr(
        "synthetic_data.worker.engine.validate_schema",
        lambda source_dataframe, synthetic_dataframe: object(),
    )

    monkeypatch.setattr(
        "synthetic_data.worker.engine.evaluate_privacy",
        lambda source_dataframe, synthetic_dataframe, detection: object(),
    )

    monkeypatch.setattr(
        "synthetic_data.worker.engine.persist_artifacts",
        lambda **kwargs: artifacts,
    )

    engine = V02Engine(tmp_path)

    result = engine.execute(
        job_id="job-001",
        input_file="input.csv",
        row_count=2,
    )

    assert result == artifacts


def test_engine_wraps_execution_errors(monkeypatch, tmp_path):
    def failing_pipeline(**kwargs):
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr(
        "synthetic_data.worker.engine.run_pipeline",
        failing_pipeline,
    )

    engine = V02Engine(tmp_path)

    with pytest.raises(EngineExecutionError, match="V0.2 engine execution failed"):
        engine.execute(
            job_id="job-001",
            input_file="input.csv",
            row_count=100,
        )