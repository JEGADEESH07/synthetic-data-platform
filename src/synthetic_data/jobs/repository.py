import sqlite3
from datetime import datetime

from synthetic_data.jobs.models import Job, JobStatus


class JobRepository:
    """SQLite persistence layer for synthetic-data jobs."""

    def __init__(self, database_path: str):
        self.database_path = database_path
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    input_file TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    synthetic_data_path TEXT,
                    report_path TEXT,
                    error_code TEXT,
                    error_message TEXT
                )
                """
            )
            connection.commit()

    def create(self, job: Job) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id,
                    input_file,
                    row_count,
                    status,
                    created_at,
                    started_at,
                    completed_at,
                    synthetic_data_path,
                    report_path,
                    error_code,
                    error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.input_file,
                    job.row_count,
                    job.status.value,
                    job.created_at.isoformat(),
                    self._serialize_datetime(job.started_at),
                    self._serialize_datetime(job.completed_at),
                    job.synthetic_data_path,
                    job.report_path,
                    job.error_code,
                    job.error_message,
                ),
            )
            connection.commit()

    def get(self, job_id: str) -> Job | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def update(self, job: Job) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE jobs
                SET
                    input_file = ?,
                    row_count = ?,
                    status = ?,
                    created_at = ?,
                    started_at = ?,
                    completed_at = ?,
                    synthetic_data_path = ?,
                    report_path = ?,
                    error_code = ?,
                    error_message = ?
                WHERE job_id = ?
                """,
                (
                    job.input_file,
                    job.row_count,
                    job.status.value,
                    job.created_at.isoformat(),
                    self._serialize_datetime(job.started_at),
                    self._serialize_datetime(job.completed_at),
                    job.synthetic_data_path,
                    job.report_path,
                    job.error_code,
                    job.error_message,
                    job.job_id,
                ),
            )
            connection.commit()

    @staticmethod
    def _serialize_datetime(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()

    @staticmethod
    def _deserialize_datetime(value: str | None) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(value)

    @classmethod
    def _row_to_job(cls, row: sqlite3.Row) -> Job:
        return Job(
            job_id=row["job_id"],
            input_file=row["input_file"],
            row_count=row["row_count"],
            status=JobStatus(row["status"]),
            created_at=cls._deserialize_datetime(row["created_at"]),
            started_at=cls._deserialize_datetime(row["started_at"]),
            completed_at=cls._deserialize_datetime(row["completed_at"]),
            synthetic_data_path=row["synthetic_data_path"],
            report_path=row["report_path"],
            error_code=row["error_code"],
            error_message=row["error_message"],
        )