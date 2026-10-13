
from synthetic_data.jobs.repository import JobRepository
from synthetic_data.jobs.service import JobService
from synthetic_data.queue.job_queue import JobQueue


def test_recovery_requeues_job_when_input_file_exists(tmp_path, monkeypatch):
    import synthetic_data.api.app as app_module

    input_file = tmp_path / "input.csv"
    input_file.write_text("id,value\n1,100\n", encoding="utf-8")

    service = JobService(JobRepository(tmp_path / "jobs.db"))
    job = service.create_job(
        job_id="recoverable-job",
        input_file=str(input_file),
        row_count=10,
    )
    service.queue_job(job.job_id)

    queue = JobQueue()
    monkeypatch.setattr(app_module, "job_service", service)
    monkeypatch.setattr(app_module, "job_queue", queue)

    app_module.recover_queued_jobs()

    recovered_job = service.get_job(job.job_id)
    assert recovered_job is not None
    assert recovered_job.status.value == "QUEUED"
    assert queue.dequeue() == job.job_id
    assert queue.dequeue() is None


def test_recovery_fails_job_when_input_file_is_missing(tmp_path, monkeypatch):
    import synthetic_data.api.app as app_module

    service = JobService(JobRepository(tmp_path / "jobs.db"))
    job = service.create_job(
        job_id="missing-input-job",
        input_file=str(tmp_path / "missing.csv"),
        row_count=10,
    )
    service.queue_job(job.job_id)

    queue = JobQueue()
    monkeypatch.setattr(app_module, "job_service", service)
    monkeypatch.setattr(app_module, "job_queue", queue)

    app_module.recover_queued_jobs()

    recovered_job = service.get_job(job.job_id)
    assert recovered_job is not None
    assert recovered_job.status.value == "FAILED"
    assert recovered_job.error_code == "INPUT_FILE_MISSING"
    assert queue.dequeue() is None


def test_recovery_twice_does_not_duplicate_queued_job(tmp_path, monkeypatch):
    import synthetic_data.api.app as app_module

    input_file = tmp_path / "input.csv"
    input_file.write_text("id,value\n1,100\n", encoding="utf-8")

    service = JobService(JobRepository(tmp_path / "jobs.db"))
    job = service.create_job(
        job_id="recover-twice-job",
        input_file=str(input_file),
        row_count=10,
    )
    service.queue_job(job.job_id)

    queue = JobQueue()
    monkeypatch.setattr(app_module, "job_service", service)
    monkeypatch.setattr(app_module, "job_queue", queue)

    app_module.recover_queued_jobs()
    app_module.recover_queued_jobs()

    assert queue.size() == 1
    assert queue.dequeue() == job.job_id
    assert queue.dequeue() is None


def test_recovery_continues_when_one_job_cannot_be_marked_failed(
    tmp_path,
    monkeypatch,
):
    import synthetic_data.api.app as app_module

    valid_input = tmp_path / "valid.csv"
    valid_input.write_text("id,value\n1,100\n", encoding="utf-8")

    service = JobService(JobRepository(tmp_path / "jobs.db"))

    missing_job = service.create_job(
        job_id="recovery-failure-job",
        input_file=str(tmp_path / "missing.csv"),
        row_count=10,
    )
    service.queue_job(missing_job.job_id)

    valid_job = service.create_job(
        job_id="recovery-valid-job",
        input_file=str(valid_input),
        row_count=10,
    )
    service.queue_job(valid_job.job_id)

    original_mark_failed = service.mark_failed

    def fail_one_recovery(job_id, **kwargs):
        if job_id == missing_job.job_id:
            raise RuntimeError("simulated database failure")
        return original_mark_failed(job_id, **kwargs)

    monkeypatch.setattr(service, "mark_failed", fail_one_recovery)

    queue = JobQueue()
    monkeypatch.setattr(app_module, "job_service", service)
    monkeypatch.setattr(app_module, "job_queue", queue)

    app_module.recover_queued_jobs()

    assert queue.dequeue() == valid_job.job_id
    assert queue.dequeue() is None

    still_queued = service.get_job(missing_job.job_id)
    assert still_queued is not None
    assert still_queued.status.value == "QUEUED"


def test_recovery_fails_interrupted_running_job_and_recovers_queued_job(
    tmp_path,
    monkeypatch,
):
    import synthetic_data.api.app as app_module

    input_file = tmp_path / "input.csv"
    input_file.write_text("id,value\n1,100\n", encoding="utf-8")

    service = JobService(JobRepository(tmp_path / "jobs.db"))

    running_job = service.create_job(
        job_id="interrupted-running-job",
        input_file=str(input_file),
        row_count=10,
    )
    service.queue_job(running_job.job_id)
    service.mark_running(running_job.job_id)

    queued_job = service.create_job(
        job_id="recoverable-queued-job",
        input_file=str(input_file),
        row_count=10,
    )
    service.queue_job(queued_job.job_id)

    queue = JobQueue()
    monkeypatch.setattr(app_module, "job_service", service)
    monkeypatch.setattr(app_module, "job_queue", queue)

    app_module.recover_queued_jobs()

    recovered_running_job = service.get_job(running_job.job_id)
    assert recovered_running_job is not None
    assert recovered_running_job.status.value == "FAILED"
    assert recovered_running_job.error_code == "STALE_JOB"
    assert "interrupted" in recovered_running_job.error_message.lower()

    recovered_queued_job = service.get_job(queued_job.job_id)
    assert recovered_queued_job is not None
    assert recovered_queued_job.status.value == "QUEUED"
    assert queue.dequeue() == queued_job.job_id
    assert queue.dequeue() is None
