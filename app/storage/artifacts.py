from pathlib import Path


class ArtifactStore:
    """
    Manages filesystem locations for job artifacts.
    """

    def __init__(
        self,
        base_path: str = "data/output/jobs",
    ) -> None:
        self.base_path = Path(base_path)

    def job_directory(self, job_id: str) -> Path:
        """
        Return and create the directory for a job.
        """

        path = self.base_path / job_id
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def synthetic_data_path(self, job_id: str) -> str:
        """
        Return the synthetic-data artifact path.
        """

        return str(
            self.job_directory(job_id)
            / "synthetic_data.csv"
        )

    def evaluation_report_path(self, job_id: str) -> str:
        """
        Return the evaluation-report artifact path.
        """

        return str(
            self.job_directory(job_id)
            / "evaluation_report.json"
        )

    def attempt_directory(
        self,
        job_id: str,
        attempt_number: int,
    ) -> Path:
        """
        Return and create the directory for a
        specific generation attempt.
        """

        path = (
            self.job_directory(job_id)
            / f"attempt_{attempt_number}"
        )

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def attempt_synthetic_data_path(
        self,
        job_id: str,
        attempt_number: int,
    ) -> str:
        """
        Return the synthetic-data artifact path
        for a specific generation attempt.
        """

        return str(
            self.attempt_directory(
                job_id,
                attempt_number,
            )
            / "synthetic_data.csv"
        )

    def attempt_evaluation_report_path(
        self,
        job_id: str,
        attempt_number: int,
    ) -> str:
        """
        Return the evaluation-report artifact path
        for a specific generation attempt.
        """

        return str(
            self.attempt_directory(
                job_id,
                attempt_number,
            )
            / "evaluation_report.json"
        )