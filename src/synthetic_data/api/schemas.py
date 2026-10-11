from pydantic import BaseModel, Field

from synthetic_data.jobs.models import JobStatus


class JobCreateRequest(BaseModel):
    input_file: str = Field(min_length=1)
    row_count: int = Field(gt=0)


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    input_file: str
    row_count: int
    created_at: str
    started_at: str | None
    completed_at: str | None
    synthetic_data_path: str | None
    report_path: str | None
    error_code: str | None
    error_message: str | None