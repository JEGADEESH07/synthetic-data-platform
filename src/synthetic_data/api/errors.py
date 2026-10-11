from fastapi import Request
from fastapi.responses import JSONResponse


class APIError(Exception):
    """Base exception for safe API errors."""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class JobNotFoundError(APIError):
    def __init__(self):
        super().__init__(
            error_code="JOB_NOT_FOUND",
            message="Job not found.",
            status_code=404,
        )


class ArtifactNotFoundAPIError(APIError):
    def __init__(self):
        super().__init__(
            error_code="ARTIFACT_NOT_FOUND",
            message="Artifact not found.",
            status_code=404,
        )


async def api_error_handler(
    request: Request,
    exc: APIError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )