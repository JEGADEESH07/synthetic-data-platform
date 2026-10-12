import pytest

from synthetic_data.api.metrics import Metrics


def test_metrics_start_at_zero():
    metrics = Metrics()

    snapshot = metrics.snapshot()

    assert snapshot.http_requests_total == 0
    assert snapshot.http_requests_completed == 0
    assert snapshot.jobs_created_total == 0
    assert snapshot.jobs_succeeded_total == 0
    assert snapshot.jobs_failed_total == 0
    assert snapshot.worker_executions_total == 0
    assert snapshot.worker_execution_duration_seconds == 0.0


def test_metrics_increment_counters():
    metrics = Metrics()

    metrics.increment_http_requests()
    metrics.increment_http_requests_completed()
    metrics.increment_jobs_created()
    metrics.increment_jobs_succeeded()
    metrics.increment_jobs_failed()
    metrics.increment_worker_executions()

    snapshot = metrics.snapshot()

    assert snapshot.http_requests_total == 1
    assert snapshot.http_requests_completed == 1
    assert snapshot.jobs_created_total == 1
    assert snapshot.jobs_succeeded_total == 1
    assert snapshot.jobs_failed_total == 1
    assert snapshot.worker_executions_total == 1


def test_metrics_accumulate_duration():
    metrics = Metrics()

    metrics.observe_worker_execution_duration(1.5)
    metrics.observe_worker_execution_duration(2.5)

    snapshot = metrics.snapshot()

    assert snapshot.worker_execution_duration_seconds == 4.0


def test_metrics_reject_negative_duration():
    metrics = Metrics()

    with pytest.raises(ValueError):
        metrics.observe_worker_execution_duration(-1.0)


def test_metrics_snapshot_is_independent():
    metrics = Metrics()

    metrics.increment_jobs_created()

    first = metrics.snapshot()

    metrics.increment_jobs_created()

    second = metrics.snapshot()

    assert first.jobs_created_total == 1
    assert second.jobs_created_total == 2


def test_metrics_reset():
    metrics = Metrics()

    metrics.increment_jobs_created()
    metrics.increment_jobs_failed()

    metrics.reset()

    snapshot = metrics.snapshot()

    assert snapshot.jobs_created_total == 0
    assert snapshot.jobs_failed_total == 0