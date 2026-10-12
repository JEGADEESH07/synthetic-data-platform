from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class JobStatus(str, Enum):
    """Lifecycle states for a synthetic-data generation job."""

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass
class Job:
    """Domain model representing one synthetic-data generation job."""

    job_id: str
    input_file: str
    row_count: int
    status: JobStatus = JobStatus.CREATED

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    input_columns: int | None = None
    execution_stage: str | None = None
    progress: int | None = None
    completed_units: int | None = None
    total_units: int | None = None

    synthetic_data_path: str | None = None
    report_path: str | None = None

    error_code: str | None = None
    error_message: str | None = None