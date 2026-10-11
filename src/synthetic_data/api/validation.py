from pathlib import Path


class JobValidationError(Exception):
    """Raised when a job request is invalid."""


def validate_job_input(
    input_file: str,
    row_count: int,
) -> None:
    if not input_file.strip():
        raise JobValidationError(
            "Input file is required."
        )

    if row_count <= 0:
        raise JobValidationError(
            "Row count must be greater than zero."
        )

    input_path = Path(input_file)

    if input_path.suffix.lower() != ".csv":
        raise JobValidationError(
            "Input file must be a CSV file."
        )

    if not input_path.is_file():
        raise JobValidationError(
            "Input file does not exist."
        )