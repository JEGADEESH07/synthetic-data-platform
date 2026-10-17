import json

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
                    input_columns INTEGER,
                    execution_stage TEXT,
                    progress INTEGER,
                    completed_units INTEGER,
                    total_units INTEGER,
                    synthetic_data_path TEXT,
                    report_path TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    execution_metadata_json TEXT
                )
                """
            )
            existing_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(jobs)")
            }
            for name, column_type in (
                ("input_columns", "INTEGER"),
                ("execution_stage", "TEXT"),
                ("progress", "INTEGER"),
                ("completed_units", "INTEGER"),
                ("total_units", "INTEGER"),
                ("execution_metadata_json", "TEXT"),
            ):
                if name not in existing_columns:
                    connection.execute(
                        f"ALTER TABLE jobs ADD COLUMN {name} {column_type}"
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
                    input_columns,
                    execution_stage,
                    progress,
                    completed_units,
                    total_units,
                    synthetic_data_path,
                    report_path,
                    error_code,
                    error_message,
                    execution_metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.input_file,
                    job.row_count,
                    job.status.value,
                    job.created_at.isoformat(),
                    self._serialize_datetime(job.started_at),
                    self._serialize_datetime(job.completed_at),
                    job.input_columns,
                    job.execution_stage,
                    job.progress,
                    job.completed_units,
                    job.total_units,
                    job.synthetic_data_path,
                    job.report_path,
                    job.error_code,
                    job.error_message,
                    json.dumps(job.execution_metadata) if job.execution_metadata is not None else None,
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


    def list_by_status(self, status: JobStatus) -> list[Job]:
        """Return persisted jobs matching a lifecycle status."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at, job_id",
                (status.value,),
            ).fetchall()

        return [self._row_to_job(row) for row in rows]


    def list_all(self) -> list[Job]:
        """Return all persisted jobs, newest first."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM jobs
                ORDER BY created_at DESC, job_id DESC
                """
            ).fetchall()

        return [self._row_to_job(row) for row in rows]


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
                    input_columns = ?,
                    execution_stage = ?,
                    progress = ?,
                    completed_units = ?,
                    total_units = ?,
                    synthetic_data_path = ?,
                    report_path = ?,
                    error_code = ?,
                    error_message = ?,
                    execution_metadata_json = ?
                WHERE job_id = ?
                """,
                (
                    job.input_file,
                    job.row_count,
                    job.status.value,
                    job.created_at.isoformat(),
                    self._serialize_datetime(job.started_at),
                    self._serialize_datetime(job.completed_at),
                    job.input_columns,
                    job.execution_stage,
                    job.progress,
                    job.completed_units,
                    job.total_units,
                    job.synthetic_data_path,
                    job.report_path,
                    job.error_code,
                    job.error_message,
                    json.dumps(job.execution_metadata) if job.execution_metadata is not None else None,
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
            input_columns=row["input_columns"],
            execution_stage=row["execution_stage"],
            progress=row["progress"],
            completed_units=row["completed_units"],
            total_units=row["total_units"],
            synthetic_data_path=row["synthetic_data_path"],
            report_path=row["report_path"],
            error_code=row["error_code"],
            error_message=row["error_message"],
            execution_metadata=json.loads(row["execution_metadata_json"]) if row["execution_metadata_json"] is not None else None
        )
