from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import json
from synthetic_data.api.metrics import Metrics
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from synthetic_data import __version__
from synthetic_data.api.errors import (
    APIError,
    ArtifactNotFoundAPIError,
    JobNotFoundError,
    JobValidationAPIError,
    api_error_handler,
    http_exception_handler,
    unexpected_exception_handler,
    validation_exception_handler,
)
from synthetic_data.api.logging import configure_api_logging
from synthetic_data.api.schemas import (
    ArtifactListResponse,
    DashboardSummaryResponse,
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
)
from synthetic_data.api.uploads import (
    UploadValidationError,
    save_uploaded_csv,
    validate_uploaded_csv,
)
from synthetic_data.api.validation import (
    JobValidationError,
    validate_job_input,
)
from synthetic_data.jobs.artifacts import (
    ArtifactManager,
    ArtifactNotFoundError,
)
from synthetic_data.jobs.repository import JobRepository
from synthetic_data.jobs.service import JobService
from synthetic_data.queue.job_queue import JobQueue
from synthetic_data.worker.background import BackgroundWorker
from synthetic_data.worker.engine import V02Engine
from synthetic_data.worker.executor import JobExecutionAdapter
from synthetic_data.worker.runtime import Worker


job_repository = JobRepository("data/output/jobs/jobs.db")
job_service = JobService(job_repository)
artifact_manager = ArtifactManager("data/output/jobs")
logger = configure_api_logging()
metrics = Metrics()
job_queue = JobQueue()

engine = V02Engine(output_root="data/output/jobs")

execution_adapter = JobExecutionAdapter(
    job_service=job_service,
    engine=engine,
)

worker = Worker(
    job_queue=job_queue,
    job_service=job_service,
    executor=execution_adapter.execute,
    metrics=metrics,
)

background_worker = BackgroundWorker(
    worker=worker,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    recover_queued_jobs()
    background_worker.start()
    try:
        yield
    finally:
        background_worker.stop()


app = FastAPI(
    title="Synthetic Data Engineering & Privacy Platform",
    version=__version__,
    description=(
        "V0.3 execution platform API for submitting synthetic data "
        "generation jobs, monitoring execution, and retrieving artifacts."
    ),
    lifespan=lifespan,
)

app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)
app.add_exception_handler(Exception, unexpected_exception_handler)



def recover_queued_jobs() -> None:
    """Recover queued jobs and fail jobs interrupted by a previous process."""
    try:
        queued_jobs = job_service.list_queued_jobs()
    except Exception:
        logger.exception("Could not list queued jobs during startup recovery")
        queued_jobs = []

    for job in queued_jobs:
        try:
            input_path = Path(job.input_file)
            if not input_path.is_file():
                job_service.mark_failed(
                    job.job_id,
                    error_code="INPUT_FILE_MISSING",
                    error_message="The queued job's input file is missing.",
                )
                logger.warning(
                    "Queued job cannot be recovered because its input file is missing",
                    extra={"job_id": job.job_id},
                )
                continue

            job_queue.enqueue(job.job_id)
            logger.info("Recovered queued job", extra={"job_id": job.job_id})
        except Exception:
            logger.exception(
                "Could not recover queued job during startup",
                extra={"job_id": job.job_id},
            )

    try:
        running_jobs = job_service.list_running_jobs()
    except Exception:
        logger.exception("Could not list running jobs during startup recovery")
        return

    for job in running_jobs:
        try:
            job_service.mark_failed(
                job.job_id,
                error_code="STALE_JOB",
                error_message=(
                    "Job execution was interrupted by a previous application process. "
                    "Submit a new job to retry."
                ),
            )
            logger.warning(
                "Interrupted running job marked as failed during startup recovery",
                extra={"job_id": job.job_id},
            )
        except Exception:
            logger.exception(
                "Could not recover interrupted running job",
                extra={"job_id": job.job_id},
            )



@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid4())

    request.state.request_id = request_id
    metrics.increment_http_requests()
    response = await call_next(request)
    metrics.increment_http_requests_completed()
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "HTTP request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
        },
    )

    return response


@app.get(
    "/api/v1/health",
    summary="Check API liveness",
    description="Returns healthy when the API process is running.",
)
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get(
    "/api/v1/readiness",
    summary="Check API readiness",
    description=(
        "Returns ready when the API can access its job repository "
        "and runtime dependencies."
    ),
)
def readiness_check() -> dict[str, str]:
    job_repository.get("__readiness_check__")

    return {"status": "ready"}

@app.get(
    "/api/v1/version",
    summary="Get API version",
    description="Returns the current API version."
)
def version() -> dict[str, str]:
    return {"version": __version__}


@app.post(
    "/api/v1/jobs",
    response_model=JobCreateResponse,
    status_code=201,
)

def create_job(request: JobCreateRequest) -> JobCreateResponse:
    try:
        validate_job_input(
            input_file=request.input_file,
            row_count=request.row_count,
        )

    except JobValidationError as exc:
        logger.warning(
            "Job validation failed",
            extra={
                "row_count": request.row_count,
                "error": str(exc),
            },
        )

        raise JobValidationAPIError(str(exc)) from exc

    job_id = str(uuid4())

    try:
        job = job_service.create_job(
            job_id=job_id,
            input_file=request.input_file,
            row_count=request.row_count,
        )
        metrics.increment_jobs_created()
        job_service.queue_job(job_id)
        job_queue.enqueue(job_id)

        job = job_service.get_job(job_id)

        logger.info(
            "Job created",
            extra={
                "job_id": job.job_id,
                "row_count": job.row_count,
            },
        )

    except Exception as exc:
        logger.exception(
            "Job creation failed",
            extra={
                "job_id": job_id,
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create job.",
        ) from exc

    return JobCreateResponse(
        job_id=job.job_id,
        status=job.status,
    )


@app.post(
    "/api/v1/jobs/upload",
    response_model=JobCreateResponse,
    status_code=201,
)
async def create_job_from_upload(
    file: UploadFile = File(...),
    row_count: int = Form(...),
) -> JobCreateResponse:
    if row_count <= 0:
        raise JobValidationAPIError(
            "Row count must be greater than zero."
        )

    input_config = _get_input_config()

    if row_count > input_config.max_output_rows:
        raise JobValidationAPIError(
            "Requested row count exceeds the configured maximum."
        )

    uploaded_path: Path | None = None

    try:
        uploaded_path = save_uploaded_csv(
            file,
            input_config,
        )

        input_columns = validate_uploaded_csv(
            uploaded_path,
            input_config,
        )

        job_id = str(uuid4())

        job = job_service.create_job(
            job_id=job_id,
            input_file=str(uploaded_path),
            row_count=row_count,
            input_columns=input_columns,
        )
        job_service.queue_job(job_id)
        metrics.increment_jobs_created()
        job_queue.enqueue(job_id)

        logger.info(
            "Job created from upload",
            extra={
                "job_id": job.job_id,
                "row_count": job.row_count,
                "input_columns": job.input_columns,
            },
        )

        return JobCreateResponse(
            job_id=job.job_id,
            status=job.status,
        )

    except UploadValidationError as exc:
        if uploaded_path is not None:
            uploaded_path.unlink(missing_ok=True)

        logger.warning(
            "Uploaded file validation failed",
            extra={
                "error": str(exc),
            },
        )

        raise JobValidationAPIError(str(exc)) from exc

    except Exception:
        if uploaded_path is not None:
            uploaded_path.unlink(missing_ok=True)

        logger.exception(
            "Failed to create job from uploaded file.",
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process uploaded file.",
        )


def _get_input_config():
    """
    Return the platform input configuration.

    H1.5 keeps the existing V0.3 configuration boundary while the
    application configuration wiring is hardened in later H1 stages.
    """

    from synthetic_data.config.settings import InputConfig

    return InputConfig()


@app.get(
    "/api/v1/dashboard/summary",
    response_model=DashboardSummaryResponse,
)
def get_dashboard_summary() -> DashboardSummaryResponse:
    jobs = job_service.list_all_jobs()
    output_root = artifact_manager.output_root.resolve()

    datasets_generated = 0
    quality_evaluations = 0
    privacy_assessments = 0

    for job in jobs:
        if job.status.value != "SUCCEEDED":
            continue

        datasets_generated += 1

        try:
            job_directory = (output_root / job.job_id).resolve()
            job_directory.relative_to(output_root)

            report_path = job_directory / "report.json"
            report_path.resolve().relative_to(job_directory)

            if not report_path.is_file():
                continue

            report = json.loads(report_path.read_text(encoding="utf-8"))

            if not isinstance(report, dict):
                continue

            if isinstance(report.get("statistical_quality"), dict):
                quality_evaluations += 1

            if isinstance(report.get("privacy"), dict):
                privacy_assessments += 1

        except (OSError, ValueError, RuntimeError):
            # Ignore missing, invalid, or unsafe report files.
            continue

    return DashboardSummaryResponse(
        datasets_generated=datasets_generated,
        quality_evaluations=quality_evaluations,
        privacy_assessments=privacy_assessments,
    )

@app.get(
    "/api/v1/jobs",
    response_model=list[JobStatusResponse],
)
def list_jobs() -> list[JobStatusResponse]:
    jobs = job_service.list_all_jobs()
    responses = []

    for job in jobs:
        duration_seconds: float | None = None

        if job.started_at is not None:
            end_time = job.completed_at or datetime.now(timezone.utc)
            duration_seconds = (
                end_time - job.started_at
            ).total_seconds()

        responses.append(
            JobStatusResponse(
                job_id=job.job_id,
                status=job.status,
                input_file=job.input_file,
                row_count=job.row_count,
                input_columns=job.input_columns,
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
                duration_seconds=duration_seconds,
                execution_stage=job.execution_stage,
                progress=job.progress,
                completed_units=job.completed_units,
                total_units=job.total_units,
                execution_metadata=job.execution_metadata,
                synthetic_data_path=job.synthetic_data_path,
                report_path=job.report_path,
                error_code=job.error_code,
                error_message=job.error_message,
            )
        )

    return responses


@app.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobStatusResponse,
)
def get_job_status(job_id: str) -> JobStatusResponse:
    job = job_service.get_job(job_id)

    if job is None:
        raise JobNotFoundError()

    duration_seconds: float | None = None

    if job.started_at is not None:
        end_time = job.completed_at or datetime.now(timezone.utc)

        duration_seconds = (
            end_time - job.started_at
        ).total_seconds()

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        input_file=job.input_file,
        row_count=job.row_count,
        input_columns=job.input_columns,
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
        duration_seconds=duration_seconds,
        execution_stage=job.execution_stage,
        progress=job.progress,
        completed_units=job.completed_units,
        total_units=job.total_units,
        execution_metadata=job.execution_metadata,
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