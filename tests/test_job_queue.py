from synthetic_data.queue.job_queue import JobQueue


def test_enqueue_and_dequeue():
    queue = JobQueue()

    queue.enqueue("job-001")

    assert queue.dequeue() == "job-001"


def test_queue_is_fifo():
    queue = JobQueue()

    queue.enqueue("job-001")
    queue.enqueue("job-002")
    queue.enqueue("job-003")

    assert queue.dequeue() == "job-001"
    assert queue.dequeue() == "job-002"
    assert queue.dequeue() == "job-003"


def test_empty_queue_returns_none():
    queue = JobQueue()

    assert queue.dequeue() is None


def test_queue_size():
    queue = JobQueue()

    assert queue.size() == 0

    queue.enqueue("job-001")
    queue.enqueue("job-002")

    assert queue.size() == 2

    queue.dequeue()

    assert queue.size() == 1