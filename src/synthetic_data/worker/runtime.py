from synthetic_data.worker.engine import EngineExecutionError

import logging
from collections.abc import Callable

from synthetic_data.jobs.service import JobService
from synthetic_data.queue.job_queue import JobQueue


logger = logging.getLogger("synthetic_data.worker")


class Worker:
    """Executes queued jobs using an injected job executor."""

    def __init__(
        self,
        job_queue: JobQueue,
        job_service: JobService,
        executor: Callable[[str], tuple[str, str]],
    ):
        self.job_queue = job_queue
        self.job_service = job_service
        self.executor = executor

    def run_once(self) -> str | None:
        """Process one queued job and return its job ID."""

        job_id = self.job_queue.dequeue()

        if job_id is None:
            return None

        try:
            logger.info(
                "Job execution started | job_id=%s",
                job_id,
            )

            self.job_service.mark_running(job_id)

            synthetic_data_path, report_path = self.executor(job_id)

            self.job_service.mark_succeeded(
                job_id,
                synthetic_data_path,
                report_path,
            )

            logger.info(
                "Job execution succeeded | job_id=%s",
                job_id,
            )

        except EngineExecutionError as exc:
            logger.exception(
                "Job execution failed | job_id=%s",
                job_id,
            )

            self.job_service.mark_failed(
                job_id,
                error_code=exc.error_code,
                error_message=str(exc),
            )

        except Exception as exc:
            logger.exception(
                "Job execution failed | job_id=%s",
                job_id,
            )

            self.job_service.mark_failed(
                job_id,
                error_code="JOB_EXECUTION_FAILED",
                error_message=str(exc),
            )

        return job_id