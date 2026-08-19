import os
import tempfile
from app.jobs.store import JobStore
from datetime import datetime, timezone
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    UploadFile,
)
from pathlib import Path

from app.ingestion.loader import SUPPORTED_EXTENSIONS
from fastapi.responses import FileResponse

from app.storage.artifacts import ArtifactStore
from fastapi import HTTPException
from app.config.settings import (
    DEFAULT_QUALITY_POLICY,
    validate_generation_parameters,
)
from app.evaluation.quality_policy import (
    decide_quality_action,
)
from app.evaluation.attempt_selector import (
    select_best_attempt,
)
from app.services.synthetic_data_service import (
    SyntheticDataService,
)


app = FastAPI(
    title="Synthetic Data Platform",
    version="0.3.0",
    description="Synthetic data generation API.",
)

job_store = JobStore()
artifact_store = ArtifactStore()

def run_generation_attempt(
    service: SyntheticDataService,
    input_path: str,
    output_rows: int,
    epochs: int,
    output_data_path: str,
    output_report_path: str,
) -> dict:
    """
    Execute one synthetic-data generation attempt.
    """

    return service.generate(
        input_path=input_path,
        output_rows=output_rows,
        epochs=epochs,
        output_data_path=output_data_path,
        output_report_path=output_report_path,
    )

def evaluate_generation_attempt(
    result: dict,
) -> tuple[dict, object]:
    """
    Evaluate one generation result and determine
    the quality decision.
    """

    quality_gate = result["evaluation"]["quality_gate"]

    decision = decide_quality_action(
        gate_passed=quality_gate["passed"],
        mode=DEFAULT_QUALITY_POLICY.mode,
    )

    return quality_gate, decision

def serialize_attempt(attempt) -> dict:
    """
    Convert a JobAttempt into an API-safe dictionary.
    """

    return {
        "attempt_id": attempt.attempt_id,
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "created_at": attempt.created_at,
        "completed_at": attempt.completed_at,
        "error": attempt.error,
        "trust_score": attempt.trust_score,
        "quality_gate": attempt.quality_gate,
        "artifacts": attempt.artifacts,
    }

def run_generation_job(
    job_id: str,
    input_path: str,
    rows: int,
    epochs: int,
    original_filename: str | None,
) -> None:
    """
    Execute a synthetic-data generation job in the background.
    """

    job = job_store.get(job_id)

    if job is None:
        return

    attempt = None

    max_attempts = max(
        1,
        DEFAULT_QUALITY_POLICY.max_regeneration_attempts,
    )

    try:
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        job_store.save(job)

        service = SyntheticDataService()

        final_result = None
        final_quality_gate = None
        final_decision = None

        for attempt_number in range(
            1,
            max_attempts + 1,
        ):
            attempt = None
            attempt = job_store.create_attempt(
                job_id=job.job_id,
                attempt_number=attempt_number,
            )

            output_data_path = (
                artifact_store.attempt_synthetic_data_path(
                    job.job_id,
                    attempt_number,
                )
            )

            output_report_path = (
                artifact_store.attempt_evaluation_report_path(
                    job.job_id,
                    attempt_number,
                )
            )

            result = run_generation_attempt(
                service=service,
                input_path=input_path,
                output_rows=rows,
                epochs=epochs,
                output_data_path=output_data_path,
                output_report_path=output_report_path,
            )

            quality_gate, decision = (
                evaluate_generation_attempt(result)
            )

            if decision.action == "complete":
                attempt.status = "completed"

            elif decision.action == "regenerate":
                attempt.status = "quality_failed"

            else:
                attempt.status = "failed"

            attempt.completed_at = datetime.now(
                timezone.utc
            )

            attempt.trust_score = (
                result["evaluation"]["trust"]["trust_score"]
            )

            attempt.quality_gate = quality_gate

            attempt.artifacts = {
                "synthetic_data": output_data_path,
                "evaluation_report": output_report_path,
            }

            job_store.save_attempt(attempt)

            final_result = result
            final_quality_gate = quality_gate
            final_decision = decision

            attempts = job_store.get_attempts(
                job.job_id
            )

            best_attempt = select_best_attempt(
                attempts
            )

            if decision.action == "complete":
                break

            if decision.action == "fail":
                break

            if decision.action == "regenerate":
                if attempt_number < max_attempts:
                    continue

                break

        attempts = job_store.get_attempts(
            job.job_id
        )

        best_attempt = select_best_attempt(
            attempts
        )

        if best_attempt is None:
            raise RuntimeError(
                "No generation attempts were recorded."
            )

        if final_decision is None:
            raise RuntimeError(
                "No quality decision was produced."
            )

        if final_decision.action == "complete":
            job.status = "completed"
            job.completed_at = datetime.now(
                timezone.utc
            )

        elif final_decision.action == "fail":
            job.status = "failed"
            job.completed_at = datetime.now(
                timezone.utc
            )
            job.error = final_decision.reason

        elif final_decision.action == "regenerate":
            job.status = "failed"
            job.completed_at = datetime.now(
                timezone.utc
            )
            job.error = (
                "Maximum regeneration attempts reached."
            )

        else:
            raise RuntimeError(
                f"Unsupported final action: "
                f"{final_decision.action}"
            )

        job.result = {
            "filename": original_filename,
            "saved_files": (
                final_result["saved_files"]
                if final_result
                else {}
            ),
            "schema_valid": (
                final_result["evaluation"]["schema"]["valid"]
                if final_result
                else False
            ),
            "privacy_safe": (
                final_result["evaluation"]["privacy"]["safe"]
                if final_result
                else False
            ),
            "trust": (
                final_result["evaluation"]["trust"]
                if final_result
                else None
            ),
            "quality_gate": final_quality_gate,
            "quality_decision": final_decision.__dict__,
            "best_attempt": {
                "attempt_id": best_attempt.attempt_id,
                "attempt_number": (
                    best_attempt.attempt_number
                ),
                "trust_score": (
                    best_attempt.trust_score
                ),
                "status": best_attempt.status,
            },
            "attempt_count": len(attempts),
            "regeneration": {
            "enabled": (
                DEFAULT_QUALITY_POLICY.mode
                == "regenerate"
            ),
            "attempts_used": len(attempts),
            "max_attempts": max_attempts,
            "regenerated": len(attempts) > 1,
            "stopping_reason": (
                "quality_gate_passed"
                if final_decision.action == "complete"
                else (
                    "maximum_attempts_reached"
                    if final_decision.action == "regenerate"
                    else final_decision.action
                )
            ),
        },
        }

        job.artifacts = best_attempt.artifacts

        job_store.save(job)

    except Exception as exc:
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        job.error = str(exc)

        if attempt is not None:
            attempt.status = "failed"
            attempt.completed_at = datetime.now(
                timezone.utc
            )
            attempt.error = str(exc)

            job_store.save_attempt(attempt)

        job_store.save(job)

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


@app.get("/health")
def health_check() -> dict:
    """
    Return the health status of the API service.
    """

    return {
        "status": "healthy"
    }


@app.get("/readiness")
def readiness_check() -> dict:
    """
    Return whether the API service is ready to accept work.
    """

    return {
        "status": "ready"
    }


@app.post("/api/v1/generate")
async def generate_synthetic_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    rows: int = Form(..., gt=0),
    epochs: int = Form(300, gt=0),
) -> dict:
    """
    Create a background synthetic-data generation job.
    """
    try:
        validate_generation_parameters(
            output_rows=rows,
            epochs=epochs,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(
            sorted(SUPPORTED_EXTENSIONS)
        )

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {extension}. "
                f"Supported types: {supported}"
            ),
        )

    file_contents = await file.read()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".csv",
    ) as temporary_file:
        temporary_file.write(file_contents)
        input_path = temporary_file.name

    job = job_store.create()

    background_tasks.add_task(
        run_generation_job,
        job.job_id,
        input_path,
        rows,
        epochs,
        file.filename,
    )

    return {
        "job_id": job.job_id,
        "status": job.status,
        "message": "Generation job created.",
    }


@app.get("/api/v1/jobs/{job_id}")
def get_job_status(job_id: str) -> dict:
    """
    Return the status of a generation job.
    """

    job = job_store.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    attempts = job_store.get_attempts(
        job_id
    )

    return {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "error": job.error,
        "result": job.result,
        "artifacts": job.artifacts,
        "selected_attempt": (
            job.result.get("best_attempt")
            if job.result
            else None
        ),
        "attempts": [
            serialize_attempt(attempt)
            for attempt in attempts
        ],
    }

@app.get(
    "/api/v1/jobs/{job_id}/attempts/{attempt_number}"
)
def get_job_attempt(
    job_id: str,
    attempt_number: int,
) -> dict:
    """
    Return a specific generation attempt.
    """

    job = job_store.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    attempts = job_store.get_attempts(job_id)

    attempt = next(
        (
            item
            for item in attempts
            if item.attempt_number == attempt_number
        ),
        None,
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Attempt not found.",
        )

    return {
        "job_id": job_id,
        "attempt": serialize_attempt(attempt),
        "selected": (
            job.result.get("best_attempt", {}).get(
                "attempt_number"
            )
            == attempt_number
            if job.result
            else False
        ),
    }

@app.get("/api/v1/jobs/{job_id}/artifacts")
def get_job_artifacts(
    job_id: str,
) -> dict:
    """
    Return the artifacts belonging to the
    selected attempt of a generation job.
    """

    job = job_store.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    if not job.artifacts:
        raise HTTPException(
            status_code=404,
            detail="No artifacts available for this job.",
        )

    selected_attempt = (
        job.result.get("best_attempt")
        if job.result
        else None
    )

    return {
        "job_id": job.job_id,
        "selected_attempt": selected_attempt,
        "artifacts": job.artifacts,
    }

@app.get(
    "/api/v1/jobs/{job_id}/artifacts/{artifact_name}"
)
def download_job_artifact(
    job_id: str,
    artifact_name: str,
):
    """
    Download an artifact belonging to the
    selected attempt of a generation job.
    """

    job = job_store.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    if not job.artifacts:
        raise HTTPException(
            status_code=404,
            detail="No artifacts available for this job.",
        )

    if artifact_name not in job.artifacts:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Artifact '{artifact_name}' "
                "was not found."
            ),
        )

    artifact_path = job.artifacts[
        artifact_name
    ]

    if not os.path.exists(artifact_path):
        raise HTTPException(
            status_code=404,
            detail="Artifact file does not exist.",
        )

    return FileResponse(
        path=artifact_path,
        filename=os.path.basename(
            artifact_path
        ),
    )