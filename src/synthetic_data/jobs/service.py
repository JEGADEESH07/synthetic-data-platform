from datetime import datetime, timezone
from pathlib import Path
from synthetic_data.jobs.models import Job, JobStatus
from synthetic_data.jobs.repository import JobRepository
import json

class JobFailureCode:
    """Stable failure categories for job execution."""

    EXECUTION_FAILED = "JOB_EXECUTION_FAILED"
    ENGINE_FAILED = "ENGINE_FAILED"
    ARTIFACT_FAILED = "ARTIFACT_FAILED"
    STALE_JOB = "STALE_JOB"
    UNKNOWN = "UNKNOWN"

class JobService:
    """Application service for synthetic-data job lifecycle management."""

    def __init__(self, repository: JobRepository):
        self.repository = repository

    def create_job(
        self,
        job_id: str,
        input_file: str,
        row_count: int,
        input_columns: int | None = None,
    ) -> Job:
        """Create and persist a new job in CREATED state."""
        job = Job(
            job_id=job_id,
            input_file=input_file,
            row_count=row_count,
            input_columns=input_columns,
        )

        self.repository.create(job)
        return job

    def get_job(self, job_id: str) -> Job | None:
        """Return a job by ID, or None when it does not exist."""
        return self.repository.get(job_id)


    def list_queued_jobs(self) -> list[Job]:
        """Return persisted jobs waiting to be executed."""
        return self.repository.list_by_status(JobStatus.QUEUED)

    def list_running_jobs(self) -> list[Job]:
        """Return persisted jobs currently marked as running."""
        return self.repository.list_by_status(JobStatus.RUNNING)

    def set_execution_metadata(
        self,
        job_id: str,
        execution_metadata: dict,
    ) -> Job:
        """Persist JSON-compatible execution metadata for a running job."""
        job = self._require_job(job_id)
        self._require_status(job, JobStatus.RUNNING)

        if not isinstance(execution_metadata, dict):
            raise ValueError("Execution metadata must be a dictionary.")

        try:
            # Round-trip to validate JSON compatibility and detach the data.
            normalized_metadata = json.loads(
                json.dumps(execution_metadata)
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Execution metadata must contain JSON-compatible values."
            ) from exc

        job.execution_metadata = normalized_metadata
        self.repository.update(job)
        return job


    def queue_job(self, job_id: str) -> Job:
        """Move a job from CREATED to QUEUED."""
        job = self._require_job(job_id)
        self._require_status(job, JobStatus.CREATED)

        job.status = JobStatus.QUEUED
        job.execution_stage = "QUEUED"
        job.progress = 0

        self.repository.update(job)
        return job

    def mark_running(self, job_id: str) -> Job:
        """Move a job from QUEUED to RUNNING."""
        job = self._require_job(job_id)
        self._require_status(job, JobStatus.QUEUED)

        job.status = JobStatus.RUNNING
        job.execution_stage = "RUNNING"
        job.progress = 0
        job.started_at = datetime.now(timezone.utc)

        self.repository.update(job)
        return job

    def update_progress(
        self,
        job_id: str,
        *,
        execution_stage: str | None = None,
        progress: int | None = None,
        completed_units: int | None = None,
        total_units: int | None = None,
    ) -> Job:
        """Update truthful execution metadata for a running job."""
        job = self._require_job(job_id)
        self._require_status(job, JobStatus.RUNNING)

        if progress is not None:
            if not isinstance(progress, int):
                raise ValueError("Progress must be an integer.")
            if progress < 0 or progress > 100:
                raise ValueError("Progress must be between 0 and 100.")

        if completed_units is not None and completed_units < 0:
            raise ValueError("Completed units cannot be negative.")

        if total_units is not None and total_units < 0:
            raise ValueError("Total units cannot be negative.")

        resolved_completed_units = (
            completed_units
            if completed_units is not None
            else job.completed_units
        )

        resolved_total_units = (
            total_units
            if total_units is not None
            else job.total_units
        )

        if (
            resolved_completed_units is not None
            and resolved_total_units is not None
            and resolved_completed_units > resolved_total_units
        ):
            raise ValueError(
                "Completed units cannot exceed total units."
            )

        if execution_stage is not None:
            if not execution_stage.strip():
                raise ValueError("Execution stage cannot be empty.")
            job.execution_stage = execution_stage

        if progress is not None:
            job.progress = progress

        if completed_units is not None:
            job.completed_units = completed_units

        if total_units is not None:
            job.total_units = total_units

        self.repository.update(job)
        return job


    def mark_succeeded(
        self,
        job_id: str,
        synthetic_data_path: str,
        report_path: str,
    ) -> Job:
        """Move a running job to SUCCEEDED only when artifacts exist."""
        job = self._require_job(job_id)
        self._require_status(job, JobStatus.RUNNING)

        synthetic_path = Path(synthetic_data_path)
        report_file = Path(report_path)

        if not synthetic_path.is_file():
            raise ValueError(
                "Synthetic data artifact does not exist."
            )

        if not report_file.is_file():
            raise ValueError(
                "Report artifact does not exist."
            )

        job.status = JobStatus.SUCCEEDED
        job.execution_stage = "COMPLETED"
        job.progress = 100
        job.synthetic_data_path = str(synthetic_path)
        job.report_path = str(report_file)
        job.completed_at = datetime.now(timezone.utc)

        self.repository.update(job)
        return job

    def mark_failed(
        self,
        job_id: str,
        error_code: str,
        error_message: str,
    ) -> Job:
        """Move a queued or running job to FAILED."""
        job = self._require_job(job_id)

        if job.status not in (
            JobStatus.QUEUED,
            JobStatus.RUNNING,
        ):
            raise ValueError(
                f"Cannot fail job in status {job.status.value}."
            )

        job.status = JobStatus.FAILED
        job.execution_stage = "FAILED"
        job.error_code = error_code
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)

        self.repository.update(job)
        return job

    def fail_stale_job(
        self,
        job_id: str,
        *,
        stale_after_seconds: int,
    ) -> Job:
        """Mark a running job as failed when its execution is stale."""
        if stale_after_seconds <= 0:
            raise ValueError("Stale threshold must be greater than zero.")

        job = self._require_job(job_id)
        self._require_status(job, JobStatus.RUNNING)

        if job.started_at is None:
            raise ValueError("Running job has no start time.")

        elapsed_seconds = (
            datetime.now(timezone.utc) - job.started_at
        ).total_seconds()

        if elapsed_seconds < stale_after_seconds:
            raise ValueError("Job is not stale.")

        job.status = JobStatus.FAILED
        job.execution_stage = "FAILED"
        job.error_code = "STALE_JOB"
        job.error_message = (
            "Job exceeded the allowed execution time."
        )
        job.completed_at = datetime.now(timezone.utc)

        self.repository.update(job)
        return job

    def _require_job(self, job_id: str) -> Job:
        """Return a job or raise when it does not exist."""
        job = self.repository.get(job_id)

        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        return job

    @staticmethod
    def _require_status(
        job: Job,
        expected_status: JobStatus,
    ) -> None:
        """Ensure a job is in the expected lifecycle state."""
        if job.status != expected_status:
            raise ValueError(
                f"Job {job.job_id} is in status "
                f"{job.status.value}; "
                f"expected {expected_status.value}."
            )
