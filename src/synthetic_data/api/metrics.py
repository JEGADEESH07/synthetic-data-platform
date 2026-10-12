from dataclasses import dataclass, field
from threading import Lock
from time import monotonic


@dataclass
class MetricsSnapshot:
    http_requests_total: int = 0
    http_requests_completed: int = 0
    jobs_created_total: int = 0
    jobs_succeeded_total: int = 0
    jobs_failed_total: int = 0
    worker_executions_total: int = 0
    worker_execution_duration_seconds: float = 0.0


@dataclass
class Metrics:
    """Small in-memory metrics abstraction for V0.3."""

    _snapshot: MetricsSnapshot = field(
        default_factory=MetricsSnapshot,
        init=False,
    )
    _lock: Lock = field(
        default_factory=Lock,
        init=False,
        repr=False,
    )

    def increment_http_requests(self) -> None:
        with self._lock:
            self._snapshot.http_requests_total += 1

    def increment_http_requests_completed(self) -> None:
        with self._lock:
            self._snapshot.http_requests_completed += 1

    def increment_jobs_created(self) -> None:
        with self._lock:
            self._snapshot.jobs_created_total += 1

    def increment_jobs_succeeded(self) -> None:
        with self._lock:
            self._snapshot.jobs_succeeded_total += 1

    def increment_jobs_failed(self) -> None:
        with self._lock:
            self._snapshot.jobs_failed_total += 1

    def increment_worker_executions(self) -> None:
        with self._lock:
            self._snapshot.worker_executions_total += 1

    def observe_worker_execution_duration(
        self,
        duration_seconds: float,
    ) -> None:
        if duration_seconds < 0:
            raise ValueError(
                "Duration cannot be negative."
            )

        with self._lock:
            self._snapshot.worker_execution_duration_seconds += (
                duration_seconds
            )

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            return MetricsSnapshot(
                http_requests_total=self._snapshot.http_requests_total,
                http_requests_completed=(
                    self._snapshot.http_requests_completed
                ),
                jobs_created_total=self._snapshot.jobs_created_total,
                jobs_succeeded_total=self._snapshot.jobs_succeeded_total,
                jobs_failed_total=self._snapshot.jobs_failed_total,
                worker_executions_total=(
                    self._snapshot.worker_executions_total
                ),
                worker_execution_duration_seconds=(
                    self._snapshot.worker_execution_duration_seconds
                ),
            )

    def reset(self) -> None:
        with self._lock:
            self._snapshot = MetricsSnapshot()


def measure_duration():
    """Return a monotonic timer for duration measurement."""
    return monotonic()