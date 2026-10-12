from time import monotonic

import logging
from collections.abc import Callable

from synthetic_data.api.metrics import Metrics
from synthetic_data.jobs.service import JobService
from synthetic_data.queue.job_queue import JobQueue
from synthetic_data.worker.engine import EngineExecutionError


logger = logging.getLogger("synthetic_data.worker")


class Worker:
    """Executes queued jobs using an injected job executor."""

    def __init__(
        self,
        job_queue: JobQueue,
        job_service: JobService,
        executor: Callable[[str], tuple[str, str]],
        metrics: Metrics | None = None,
    ):
        self.job_queue = job_queue
        self.job_service = job_service
        self.executor = executor
        self.metrics = metrics or Metrics()

    def run_once(self) -> str | None:
        """Process one queued job and return its job ID."""

        job_id = self.job_queue.dequeue()

        if job_id is None:
            logger.debug("Worker queue is empty.")
            return None

        start_time = monotonic()
        self.metrics.increment_worker_executions()

        logger.info(
            "Worker picked up job | job_id=%s",
            job_id,
        )

        try:
            self.job_service.mark_running(job_id)

            logger.info(
                "Job execution started | job_id=%s",
                job_id,
            )

            synthetic_data_path, report_path = self.executor(job_id)

            self.job_service.mark_succeeded(
                job_id,
                synthetic_data_path,
                report_path,
            )

            self.metrics.increment_jobs_succeeded()

            duration_seconds = monotonic() - start_time

            logger.info(
                "Job execution succeeded | "
                "job_id=%s | duration_seconds=%.3f",
                job_id,
                duration_seconds,
            )

        except EngineExecutionError as exc:
            self.metrics.increment_jobs_failed()

            duration_seconds = monotonic() - start_time

            logger.exception(
                "Job execution failed | "
                "job_id=%s | error_code=%s | duration_seconds=%.3f",
                job_id,
                exc.error_code,
                duration_seconds,
            )

            self.job_service.mark_failed(
                job_id,
                error_code=exc.error_code,
                error_message=str(exc),
            )

            logger.info(
                "Job marked failed | "
                "job_id=%s | error_code=%s",
                job_id,
                exc.error_code,
            )

        except Exception as exc:
            self.metrics.increment_jobs_failed()

            duration_seconds = monotonic() - start_time

            logger.exception(
                "Job execution failed | "
                "job_id=%s | error_code=JOB_EXECUTION_FAILED | "
                "duration_seconds=%.3f",
                job_id,
                duration_seconds,
            )

            self.job_service.mark_failed(
                job_id,
                error_code="JOB_EXECUTION_FAILED",
                error_message=str(exc),
            )

            logger.info(
                "Job marked failed | "
                "job_id=%s | error_code=JOB_EXECUTION_FAILED",
                job_id,
            )

        finally:
            self.metrics.observe_worker_execution_duration(
                monotonic() - start_time
            )

        return job_id