from uuid import uuid4

from fastapi import FastAPI, HTTPException

from synthetic_data import __version__
from synthetic_data.api.schemas import JobCreateRequest, JobCreateResponse
from synthetic_data.jobs.repository import JobRepository
from synthetic_data.jobs.service import JobService


app = FastAPI(
    title="Synthetic Data Engineering & Privacy Platform",
    version=__version__,
    description="V0.3 execution platform API.",
)


job_repository = JobRepository("data/output/jobs/jobs.db")
job_service = JobService(job_repository)


@app.get("/api/v1/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/v1/version")
def version() -> dict[str, str]:
    return {"version": __version__}


@app.post(
    "/api/v1/jobs",
    response_model=JobCreateResponse,
    status_code=201,
)
def create_job(request: JobCreateRequest) -> JobCreateResponse:
    job_id = str(uuid4())

    try:
        job = job_service.create_job(
            job_id=job_id,
            input_file=request.input_file,
            row_count=request.row_count,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to create job.",
        ) from exc

    return JobCreateResponse(
        job_id=job.job_id,
        status=job.status,
    )