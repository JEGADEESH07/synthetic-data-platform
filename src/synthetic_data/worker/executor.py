
"""Adapts persisted jobs to the V0.2 engine execution contract."""

import json
from pathlib import Path

from synthetic_data.jobs.service import JobService
from synthetic_data.worker.engine import V02Engine


class JobExecutionAdapter:
    """Adapts persisted jobs to the V0.2 engine execution contract."""

    def __init__(self, job_service: JobService, engine: V02Engine):
        self.job_service = job_service
        self.engine = engine

    def execute(self, job_id: str) -> tuple[str, str]:
        job = self.job_service.get_job(job_id)

        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        artifacts = self.engine.execute(
            job_id=job.job_id,
            input_file=job.input_file,
            row_count=job.row_count,
        )

        report_path = Path(artifacts.report_path)

        try:
            report = json.loads(
                report_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Could not read audit report for job {job_id}"
            ) from exc

        audit = report.get("audit")
        if not isinstance(audit, dict):
            raise RuntimeError(
                f"Audit metadata missing or invalid for job {job_id}"
            )

        engine_metadata = audit.get("engine", {})
        reproducibility = audit.get("reproducibility", {})
        execution = audit.get("execution", {})
        dataset = audit.get("dataset", {})

        summary = {
            "engine_version": engine_metadata.get("engine_version"),
            "seed": reproducibility.get("seed"),
            "ctgan_epochs": reproducibility.get("ctgan_epochs"),
            "requested_row_count": execution.get("requested_row_count"),
            "generated_row_count": execution.get("generated_row_count"),
            "source_schema_fingerprint": dataset.get(
                "source_schema_fingerprint"
            ),
            "source_dataset_fingerprint": dataset.get(
                "source_dataset_fingerprint"
            ),
            "synthetic_schema_fingerprint": dataset.get(
                "synthetic_schema_fingerprint"
            ),
            "synthetic_dataset_fingerprint": dataset.get(
                "synthetic_dataset_fingerprint"
            ),
        }

        self.job_service.set_execution_metadata(job_id, summary)

        return (
            str(artifacts.synthetic_data_path),
            str(artifacts.report_path),
        )
