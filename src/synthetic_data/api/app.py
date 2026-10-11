from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from synthetic_data import __version__
from synthetic_data.api.errors import (
    APIError,
    ArtifactNotFoundAPIError,
    JobNotFoundError,
    api_error_handler,
)
from synthetic_data.api.schemas import (
    ArtifactListResponse,
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
)
from synthetic_data.jobs.artifacts import (
    ArtifactManager,
    ArtifactNotFoundError,
)
from synthetic_data.jobs.repository import JobRepository
from synthetic_data.jobs.service import JobService


app = FastAPI(
    title="Synthetic Data Engineering & Privacy Platform",
    version=__version__,
    description="V0.3 execution platform API.",
)

app.add_exception_handler(APIError, api_error_handler)


job_repository = JobRepository("data/output/jobs/jobs.db")
job_service = JobService(job_repository)
artifact_manager = ArtifactManager("data/output/jobs")


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


@app.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobStatusResponse,
)
def get_job_status(job_id: str) -> JobStatusResponse:
    job = job_service.get_job(job_id)

    if job is None:
        raise JobNotFoundError()

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        input_file=job.input_file,
        row_count=job.row_count,
        created_at=job.created_at.isoformat(),
        started_at=(
            job.started_at.isoformat()
            if job.started_at is not None
            else None
        ),
        completed_at=(
            job.completed_at.isoformat()
            if job.completed_at is not None
            else None
        ),
        synthetic_data_path=job.synthetic_data_path,
        report_path=job.report_path,
        error_code=job.error_code,
        error_message=job.error_message,
    )


@app.get(
    "/api/v1/jobs/{job_id}/artifacts",
    response_model=ArtifactListResponse,
)
def list_job_artifacts(job_id: str) -> ArtifactListResponse:
    job = job_service.get_job(job_id)

    if job is None:
        raise JobNotFoundError()

    try:
        artifacts = artifact_manager.get_artifacts(job_id)
    except ArtifactNotFoundError:
        raise ArtifactNotFoundAPIError()

    return ArtifactListResponse(
        job_id=job_id,
        artifacts=[
            artifacts.synthetic_data_path.name,
            artifacts.report_path.name,
        ],
    )


@app.get(
    "/api/v1/jobs/{job_id}/artifacts/{artifact_name}",
)
def get_job_artifact(
    job_id: str,
    artifact_name: str,
):
    job = job_service.get_job(job_id)

    if job is None:
        raise JobNotFoundError()

    try:
        artifacts = artifact_manager.get_artifacts(job_id)
    except ArtifactNotFoundError:
        raise ArtifactNotFoundAPIError()

    artifact_paths = {
        "synthetic_data.csv": artifacts.synthetic_data_path,
        "report.json": artifacts.report_path,
    }

    artifact_path = artifact_paths.get(artifact_name)

    if artifact_path is None:
        raise ArtifactNotFoundAPIError()

    return FileResponse(
        path=artifact_path,
        filename=artifact_path.name,
    )