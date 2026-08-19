from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class Job:
    """
    Represents a synthetic-data generation job.
    """

    job_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    status: str = "queued"

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None

    error: str | None = None

    result: dict[str, Any] | None = None

    artifacts: dict[str, str] = field(
        default_factory=dict
    )