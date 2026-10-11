from queue import Empty, Queue


class JobQueue:
    """In-memory FIFO queue for V0.3 job execution."""

    def __init__(self):
        self._queue: Queue[str] = Queue()

    def enqueue(self, job_id: str) -> None:
        self._queue.put(job_id)

    def dequeue(self) -> str | None:
        try:
            return self._queue.get_nowait()
        except Empty:
            return None

    def size(self) -> int:
        return self._queue.qsize()