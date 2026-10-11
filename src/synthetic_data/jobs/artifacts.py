from dataclasses import dataclass
from pathlib import Path


class ArtifactNotFoundError(Exception):
    """Raised when a requested job artifact does not exist."""


@dataclass(frozen=True)
class JobArtifacts:
    """Artifacts associated with a completed job."""

    job_id: str
    output_directory: Path
    synthetic_data_path: Path
    report_path: Path


class ArtifactManager:
    """Resolves and validates artifacts produced for jobs."""

    def __init__(self, output_root: str | Path = "data/output/jobs"):
        self.output_root = Path(output_root)

    def get_artifacts(self, job_id: str) -> JobArtifacts:
        output_directory = self.output_root / job_id

        if not output_directory.is_dir():
            raise ArtifactNotFoundError(
                f"Artifacts not found for job {job_id}."
            )

        synthetic_data_path = output_directory / "synthetic_data.csv"
        report_path = output_directory / "report.json"

        if not synthetic_data_path.is_file():
            raise ArtifactNotFoundError(
                f"Synthetic data artifact not found for job {job_id}."
            )

        if not report_path.is_file():
            raise ArtifactNotFoundError(
                f"Report artifact not found for job {job_id}."
            )

        return JobArtifacts(
            job_id=job_id,
            output_directory=output_directory,
            synthetic_data_path=synthetic_data_path,
            report_path=report_path,
        )