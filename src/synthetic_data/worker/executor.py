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

        return (
            str(artifacts.synthetic_data_path),
            str(artifacts.report_path),
        )