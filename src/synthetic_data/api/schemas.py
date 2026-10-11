from pydantic import BaseModel, Field

from synthetic_data.jobs.models import JobStatus


class JobCreateRequest(BaseModel):
    input_file: str = Field(min_length=1)
    row_count: int = Field(gt=0)


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus