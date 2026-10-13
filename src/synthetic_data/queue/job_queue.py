
from queue import Empty, Queue
from threading import Lock


class JobQueue:
    """Thread-safe in-memory FIFO queue with duplicate prevention."""

    def __init__(self):
        self._queue: Queue[str] = Queue()
        self._queued_ids: set[str] = set()
        self._lock = Lock()

    def enqueue(self, job_id: str) -> None:
        """Enqueue a job unless its ID is already waiting in the queue."""
        with self._lock:
            if job_id in self._queued_ids:
                return

            self._queued_ids.add(job_id)
            self._queue.put(job_id)

    def dequeue(self) -> str | None:
        """Remove and return the next queued job ID."""
        try:
            job_id = self._queue.get_nowait()
        except Empty:
            return None

        with self._lock:
            self._queued_ids.discard(job_id)

        return job_id

    def size(self) -> int:
        """Return the number of jobs currently waiting."""
        return self._queue.qsize()
