import logging
import threading
import time
from collections.abc import Callable

from synthetic_data.worker.runtime import Worker


logger = logging.getLogger("synthetic_data.worker")


class BackgroundWorker:
    """Runs the job worker continuously in a background thread."""

    def __init__(
        self,
        worker: Worker,
        poll_interval: float = 0.1,
    ) -> None:
        self.worker = worker
        self.poll_interval = poll_interval

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the background worker thread."""

        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="synthetic-data-worker",
            daemon=True,
        )

        self._thread.start()

        logger.info("Background worker started")

    def stop(self) -> None:
        """Stop the background worker thread."""

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=5)

        self._thread = None

        logger.info("Background worker stopped")

    def _run(self) -> None:
        """Continuously process queued jobs until shutdown."""

        while not self._stop_event.is_set():
            try:
                job_id = self.worker.run_once()

                if job_id is None:
                    time.sleep(self.poll_interval)

            except Exception:
                logger.exception("Unexpected background worker failure")
                time.sleep(self.poll_interval)