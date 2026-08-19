from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class JobAttempt:
    """
    Represents one synthetic-data generation attempt
    belonging to a parent job.
    """

    attempt_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    job_id: str = ""

    attempt_number: int = 1

    status: str = "running"

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    completed_at: datetime | None = None

    error: str | None = None

    trust_score: float | None = None

    quality_gate: dict[str, Any] = field(
        default_factory=dict
    )

    artifacts: dict[str, str] = field(
        default_factory=dict
    )