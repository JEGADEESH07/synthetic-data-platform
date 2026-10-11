"""Persistence of synthetic-data generation artifacts."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from synthetic_data.privacy import PrivacyReport
from synthetic_data.validation import SchemaValidationResult


class ArtifactPersistenceError(Exception):
    """Raised when generated artifacts cannot be persisted."""


@dataclass(frozen=True)
class ArtifactPaths:
    """Paths to persisted artifacts for one generation run."""

    job_id: str
    output_directory: Path
    synthetic_data_path: Path
    report_path: Path


def create_job_id() -> str:
    """Create a unique identifier for a generation job."""

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    unique_part = uuid4().hex[:8]

    return f"job_{timestamp}_{unique_part}"


def _build_report(
    job_id: str,
    synthetic_dataframe: pd.DataFrame,
    schema_result: SchemaValidationResult,
    privacy_report: PrivacyReport,
) -> dict:
    """Build a JSON-serializable run report."""

    return {
        "job_id": job_id,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "synthetic_data": {
            "row_count": len(synthetic_dataframe),
            "column_count": len(
                synthetic_dataframe.columns
            ),
            "columns": list(
                synthetic_dataframe.columns
            ),
        },
        "schema_validation": {
            "valid": schema_result.valid,
            "row_count": schema_result.row_count,
            "column_count": schema_result.column_count,
            "columns": list(schema_result.columns),
        },
        "privacy": {
            "status": privacy_report.status,
            "total_exact_matches": (
                privacy_report.total_exact_matches
            ),
            "matched_columns": list(
                privacy_report.matched_columns
            ),
            "duplicate_row_count": (
                privacy_report
                .duplicates
                .duplicate_row_count
            ),
            "duplicate_row_rate": (
                privacy_report
                .duplicates
                .duplicate_row_rate
            ),
            "identifier_results": [
                {
                    "column_name": result.column_name,
                    "source_unique_count": (
                        result.source_unique_count
                    ),
                    "synthetic_unique_count": (
                        result.synthetic_unique_count
                    ),
                    "exact_match_count": (
                        result.exact_match_count
                    ),
                    "exact_match_rate": (
                        result.exact_match_rate
                    ),
                }
                for result in (
                    privacy_report.identifier_results
                )
            ],
        },
    }


def persist_artifacts(
    synthetic_dataframe: pd.DataFrame,
    schema_result: SchemaValidationResult,
    privacy_report: PrivacyReport,
    output_root: str | Path = "data/output/jobs",
    job_id: str | None = None,
) -> ArtifactPaths:
    """Persist synthetic data and its evaluation report."""

    if not isinstance(
        synthetic_dataframe,
        pd.DataFrame,
    ):
        raise TypeError(
            "synthetic_dataframe must be a pandas DataFrame"
        )

    if not isinstance(
        schema_result,
        SchemaValidationResult,
    ):
        raise TypeError(
            "schema_result must be a SchemaValidationResult"
        )

    if not isinstance(
        privacy_report,
        PrivacyReport,
    ):
        raise TypeError(
            "privacy_report must be a PrivacyReport"
        )

    if synthetic_dataframe.empty:
        raise ArtifactPersistenceError(
            "Cannot persist an empty synthetic dataset"
        )

    resolved_job_id = (
        job_id
        if job_id is not None
        else create_job_id()
    )

    root = Path(output_root)

    output_directory = (
        root / resolved_job_id
    )

    try:
        output_directory.mkdir(
            parents=True,
            exist_ok=False,
        )

        synthetic_data_path = (
            output_directory
            / "synthetic_data.csv"
        )

        report_path = (
            output_directory
            / "report.json"
        )

        synthetic_dataframe.to_csv(
            synthetic_data_path,
            index=False,
        )

        report = _build_report(
            job_id=resolved_job_id,
            synthetic_dataframe=synthetic_dataframe,
            schema_result=schema_result,
            privacy_report=privacy_report,
        )

        report_path.write_text(
            json.dumps(
                report,
                indent=2,
            ),
            encoding="utf-8",
        )

    except Exception as exc:
        raise ArtifactPersistenceError(
            "Failed to persist generation artifacts"
        ) from exc

    return ArtifactPaths(
        job_id=resolved_job_id,
        output_directory=output_directory,
        synthetic_data_path=synthetic_data_path,
        report_path=report_path,
    )