import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.config.settings import DEFAULT_CONFIG
from app.jobs.models import Job


class JobStore:
    """
    Persistent SQLite store for generation jobs.
    """

    def __init__(
        self,
        database_path: str = DEFAULT_CONFIG.job_database_path,
    ) -> None:
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        """
        Create a database connection.
        """

        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = sqlite3.Row

        return connection

    def _initialize_database(self) -> None:
        """
        Create the jobs table if it does not exist.
        """

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    error TEXT,
                    result TEXT,
                    artifacts TEXT
                )
                """
            )

            connection.commit()
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS job_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    error TEXT,
                    trust_score REAL,
                    quality_gate TEXT,
                    artifacts TEXT,
                    FOREIGN KEY (job_id)
                        REFERENCES jobs(job_id)
                )
                """
            )
    def create(self) -> Job:
        """
        Create and persist a new job.
        """

        job = Job()

        self.save(job)

        return job

    def get(
        self,
        job_id: str,
    ) -> Job | None:
        """
        Retrieve a job by its ID.
        """

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    job_id,
                    status,
                    created_at,
                    started_at,
                    completed_at,
                    error,
                    result,
                    artifacts
                FROM jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def save(self, job: Job) -> None:
        """
        Create or update a persisted job.
        """

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO jobs (
                    job_id,
                    status,
                    created_at,
                    started_at,
                    completed_at,
                    error,
                    result,
                    artifacts
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.status,
                    job.created_at.isoformat(),
                    (
                        job.started_at.isoformat()
                        if job.started_at
                        else None
                    ),
                    (
                        job.completed_at.isoformat()
                        if job.completed_at
                        else None
                    ),
                    job.error,
                    json.dumps(
                        job.result,
                        default=str,
                    ),
                    json.dumps(
                        job.artifacts,
                        default=str,
                    ),
                ),
            )

            connection.commit()

    def save_attempt(
        self,
        attempt,
    ) -> None:
        """
        Create or update a persisted job attempt.
        """

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO job_attempts (
                    attempt_id,
                    job_id,
                    attempt_number,
                    status,
                    created_at,
                    completed_at,
                    error,
                    trust_score,
                    quality_gate,
                    artifacts
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt.attempt_id,
                    attempt.job_id,
                    attempt.attempt_number,
                    attempt.status,
                    attempt.created_at.isoformat(),
                    (
                        attempt.completed_at.isoformat()
                        if attempt.completed_at
                        else None
                    ),
                    attempt.error,
                    attempt.trust_score,
                    json.dumps(
                        attempt.quality_gate,
                        default=str,
                    ),
                    json.dumps(
                        attempt.artifacts,
                        default=str,
                    ),
                ),
            )

            connection.commit()

    def create_attempt(
        self,
        job_id: str,
        attempt_number: int,
    ):
        """
        Create and persist a new generation attempt.
        """

        from app.jobs.attempts import JobAttempt

        attempt = JobAttempt(
            job_id=job_id,
            attempt_number=attempt_number,
        )

        self.save_attempt(attempt)

        return attempt

    def get_attempt(
        self,
        attempt_id: str,
    ):
        """
        Retrieve a generation attempt by ID.
        """

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    attempt_id,
                    job_id,
                    attempt_number,
                    status,
                    created_at,
                    completed_at,
                    error,
                    trust_score,
                    quality_gate,
                    artifacts
                FROM job_attempts
                WHERE attempt_id = ?
                """,
                (attempt_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_attempt(row)

    def get_attempts(
        self,
        job_id: str,
    ) -> list:
        """
        Retrieve all attempts belonging to a job.
        """

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    attempt_id,
                    job_id,
                    attempt_number,
                    status,
                    created_at,
                    completed_at,
                    error,
                    trust_score,
                    quality_gate,
                    artifacts
                FROM job_attempts
                WHERE job_id = ?
                ORDER BY attempt_number ASC
                """,
                (job_id,),
            ).fetchall()

        return [
            self._row_to_attempt(row)
            for row in rows
        ]

    def _row_to_attempt(
        self,
        row: sqlite3.Row,
    ):
        """
        Convert a database row into a JobAttempt.
        """

        from app.jobs.attempts import JobAttempt

        return JobAttempt(
            attempt_id=row["attempt_id"],
            job_id=row["job_id"],
            attempt_number=row["attempt_number"],
            status=row["status"],
            created_at=datetime.fromisoformat(
                row["created_at"]
            ),
            completed_at=(
                datetime.fromisoformat(
                    row["completed_at"]
                )
                if row["completed_at"]
                else None
            ),
            error=row["error"],
            trust_score=row["trust_score"],
            quality_gate=json.loads(
                row["quality_gate"]
            )
            if row["quality_gate"]
            else {},
            artifacts=json.loads(
                row["artifacts"]
            )
            if row["artifacts"]
            else {},
        )

    def _row_to_job(
            self,
            row: sqlite3.Row,
        ) -> Job:
            """
            Convert a database row into a Job object.
            """

            return Job(
                job_id=row["job_id"],
                status=row["status"],
                created_at=datetime.fromisoformat(
                    row["created_at"]
                ),
                started_at=(
                    datetime.fromisoformat(
                        row["started_at"]
                    )
                    if row["started_at"]
                    else None
                ),
                completed_at=(
                    datetime.fromisoformat(
                        row["completed_at"]
                    )
                    if row["completed_at"]
                    else None
                ),
                error=row["error"],
                result=(
                    json.loads(row["result"])
                    if row["result"]
                    else None
                ),
                artifacts=(
                    json.loads(row["artifacts"])
                    if row["artifacts"]
                    else {}
                ),
        )