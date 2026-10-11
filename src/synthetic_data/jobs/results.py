from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JobResult:
    """Result produced by a successfully completed job."""

    job_id: str
    synthetic_data_path: Path
    report_path: Path