"""Secure storage helpers for uploaded input files."""

import csv
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from synthetic_data.config.settings import InputConfig


class UploadValidationError(Exception):
    """Raised when an uploaded file cannot be safely accepted."""


_CHUNK_SIZE = 1024 * 1024


def save_uploaded_csv(
    upload_file: UploadFile,
    config: InputConfig,
) -> Path:
    """
    Store an uploaded CSV file inside the controlled input boundary.

    The original filename is treated as untrusted input and is never
    used as the stored filename.
    """

    filename = upload_file.filename

    if not filename or not filename.strip():
        raise UploadValidationError(
            "Uploaded file must have a filename."
        )

    if Path(filename).suffix.lower() != ".csv":
        raise UploadValidationError(
            "Uploaded file must be a CSV file."
        )

    upload_root = (
        config.allowed_root / "uploads"
    ).resolve()

    allowed_root = config.allowed_root.resolve()

    try:
        upload_root.relative_to(allowed_root)
    except ValueError as exc:
        raise UploadValidationError(
            "Upload storage location is invalid."
        ) from exc

    upload_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    upload_id = str(uuid4())

    final_path = upload_root / f"{upload_id}.csv"
    temporary_path = upload_root / f".{upload_id}.part"

    max_file_size = (
        config.max_file_size_mb * 1024 * 1024
    )

    total_bytes = 0

    try:
        with temporary_path.open("wb") as destination:
            while True:
                chunk = upload_file.file.read(_CHUNK_SIZE)

                if not chunk:
                    break

                total_bytes += len(chunk)

                if total_bytes > max_file_size:
                    raise UploadValidationError(
                        "Uploaded file exceeds the maximum allowed size."
                    )

                destination.write(chunk)

        resolved_temporary_path = temporary_path.resolve()

        try:
            resolved_temporary_path.relative_to(
                allowed_root
            )
        except ValueError as exc:
            raise UploadValidationError(
                "Uploaded file is outside the allowed input boundary."
            ) from exc

        resolved_temporary_path.replace(final_path)

        return final_path

    except UploadValidationError:
        if temporary_path.exists():
            temporary_path.unlink()
        raise

    except OSError as exc:
        if temporary_path.exists():
            temporary_path.unlink()

        raise UploadValidationError(
            "Unable to store uploaded file."
        ) from exc


def validate_uploaded_csv(
    file_path: Path,
    config: InputConfig,
) -> None:
    """
    Validate the stored upload against CSV integrity and row limits.

    The file has already passed the upload size boundary. This function
    validates the actual stored CSV before it can become a job input.
    """

    try:
        with file_path.open(
            "r",
            encoding=config.encoding,
            newline="",
        ) as source:
            reader = csv.reader(source)

            try:
                headers = next(reader)
            except StopIteration as exc:
                raise UploadValidationError(
                    "Uploaded CSV contains no columns."
                ) from exc

            if not headers:
                raise UploadValidationError(
                    "Uploaded CSV contains no columns."
                )

            if config.reject_duplicate_columns:
                if len(headers) != len(set(headers)):
                    raise UploadValidationError(
                        "Uploaded CSV contains duplicate column names."
                    )

            row_count = 0

            for row in reader:
                row_count += 1

                if row_count > config.max_input_rows:
                    raise UploadValidationError(
                        "Uploaded CSV exceeds the maximum allowed row limit."
                    )

    except UnicodeDecodeError as exc:
        raise UploadValidationError(
            "Uploaded file encoding is invalid."
        ) from exc

    except csv.Error as exc:
        raise UploadValidationError(
            "Uploaded CSV is malformed."
        ) from exc

    except OSError as exc:
        raise UploadValidationError(
            "Unable to validate uploaded file."
        ) from exc