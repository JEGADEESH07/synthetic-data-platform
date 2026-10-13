
"""Adapter between the V0.3 worker and the frozen V0.2 engine."""

from pathlib import Path
from time import perf_counter
from typing import Any

from synthetic_data.audit import (
    capture_configuration,
    capture_engine_version,
    capture_environment,
    fingerprint_dataset,
    fingerprint_schema,
)
from synthetic_data.config import load_config
from synthetic_data.persistence import ArtifactPaths, persist_artifacts
from synthetic_data.privacy import evaluate_privacy
from synthetic_data.validation import validate_schema
from synthetic_data.pipeline import run_pipeline


class EngineExecutionError(Exception):
    """Raised when the V0.2 engine execution fails."""

    error_code = "ENGINE_FAILED"


class V02Engine:
    """Adapter between the V0.3 worker and the frozen V0.2 engine."""

    def __init__(
        self,
        output_root: str | Path = "data/output/jobs",
        config_path: str | Path = "config/default.yaml",
    ):
        self.output_root = Path(output_root)
        self.config_path = Path(config_path)

    def execute(
        self,
        job_id: str,
        input_file: str | Path,
        row_count: int,
    ) -> ArtifactPaths:
        """Execute the pipeline and persist its audit metadata."""

        started = perf_counter()

        try:
            config = load_config(self.config_path)

            result = run_pipeline(
                file_path=input_file,
                row_count=row_count,
                config=config,
            )

            synthetic_dataframe = result.synthetic_dataframe

            schema_result = validate_schema(
                source_dataframe=result.source_dataframe,
                synthetic_dataframe=synthetic_dataframe,
            )

            privacy_report = evaluate_privacy(
                source_dataframe=result.source_dataframe,
                synthetic_dataframe=synthetic_dataframe,
                detection=result.detection,
            )

            audit_metadata: dict[str, Any] = {
                "engine": capture_engine_version(),
                "environment": capture_environment(),
                "configuration": capture_configuration(config),
                "dataset": {
                    "source_schema_fingerprint": fingerprint_schema(
                        result.source_dataframe
                    ),
                    "source_dataset_fingerprint": fingerprint_dataset(
                        result.source_dataframe
                    ),
                    "synthetic_schema_fingerprint": fingerprint_schema(
                        synthetic_dataframe
                    ),
                    "synthetic_dataset_fingerprint": fingerprint_dataset(
                        synthetic_dataframe
                    ),
                },
                "execution": {
                    "requested_row_count": row_count,
                    "generated_row_count": len(synthetic_dataframe),
                    "pipeline_and_evaluation_duration_seconds": round(
                        perf_counter() - started,
                        6,
                    ),
                },
                "reproducibility": {
                    "seed": config.generation.seed,
                    "ctgan_epochs": config.generation.ctgan_epochs,
                    "note": (
                        "Seed and epoch settings are recorded for traceability; "
                        "identical output across independent training runs "
                        "has not been guaranteed."
                    ),
                },
            }

            return persist_artifacts(
                synthetic_dataframe=synthetic_dataframe,
                schema_result=schema_result,
                privacy_report=privacy_report,
                output_root=self.output_root,
                job_id=job_id,
                audit_metadata=audit_metadata,
            )

        except Exception as exc:
            raise EngineExecutionError(
                f"V0.2 engine execution failed for job {job_id}"
            ) from exc
