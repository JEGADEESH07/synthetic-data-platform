from datetime import datetime, timezone

from synthetic_data.jobs.models import Job, JobStatus
from synthetic_data.jobs.repository import JobRepository


class JobService:
    """Application service responsible for job lifecycle management."""

    def __init__(self, repository: JobRepository):
        self.repository = repository

    def create_job(
        self,
        job_id: str,
        input_file: str,
        row_count: int,
    ) -> Job:
        job = Job(
            job_id=job_id,
            input_file=input_file,
            row_count=row_count,
        )

        self.repository.create(job)
        return job

    def get_job(self, job_id: str) -> Job | None:
        return self.repository.get(job_id)

    def queue_job(self, job_id: str) -> Job:
        job = self._require_job(job_id)

        self._require_status(job, JobStatus.CREATED)

        job.status = JobStatus.QUEUED
        self.repository.update(job)

        return job

    def mark_running(self, job_id: str) -> Job:
        job = self._require_job(job_id)

        self._require_status(job, JobStatus.QUEUED)

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        self.repository.update(job)

        return job

    def mark_succeeded(
        self,
        job_id: str,
        synthetic_data_path: str,
        report_path: str,
    ) -> Job:
        job = self._require_job(job_id)

        self._require_status(job, JobStatus.RUNNING)

        job.status = JobStatus.SUCCEEDED
        job.synthetic_data_path = synthetic_data_path
        job.report_path = report_path
        job.completed_at = datetime.now(timezone.utc)

        self.repository.update(job)

        return job

    def mark_failed(
        self,
        job_id: str,
        error_code: str,
        error_message: str,
    ) -> Job:
        job = self._require_job(job_id)

        if job.status not in (
            JobStatus.QUEUED,
            JobStatus.RUNNING,
        ):
            raise ValueError(
                f"Cannot fail job in status {job.status.value}."
            )

        job.status = JobStatus.FAILED
        job.error_code = error_code
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)

        self.repository.update(job)

        return job

    def _require_job(self, job_id: str) -> Job:
        job = self.repository.get(job_id)

        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        return job

    @staticmethod
    def _require_status(
        job: Job,
        expected_status: JobStatus,
    ) -> None:
        if job.status != expected_status:
            raise ValueError(
                f"Job {job.job_id} is in status "
                f"{job.status.value}; expected "
                f"{expected_status.value}."
            )