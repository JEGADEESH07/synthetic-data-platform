from pathlib import Path

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
    ):
        self.output_root = Path(output_root)

    def execute(
        self,
        job_id: str,
        input_file: str | Path,
        row_count: int,
    ) -> ArtifactPaths:
        """Execute the existing V0.2 pipeline for a V0.3 job."""

        try:
            result = run_pipeline(
                file_path=input_file,
                row_count=row_count,
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

            artifacts = persist_artifacts(
                synthetic_dataframe=synthetic_dataframe,
                schema_result=schema_result,
                privacy_report=privacy_report,
                output_root=self.output_root,
                job_id=job_id,
            )

            return artifacts

        except Exception as exc:
            raise EngineExecutionError(
                f"V0.2 engine execution failed for job {job_id}"
            ) from exc