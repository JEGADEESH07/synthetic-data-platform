from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class APIError(Exception):
    """Base exception for expected API errors."""

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


class JobValidationAPIError(APIError):
    def __init__(self, message: str):
        super().__init__(
            error_code="JOB_VALIDATION_ERROR",
            message=message,
            status_code=400,
        )


def _request_id(request: Request) -> str | None:
    return getattr(
        request.state,
        "request_id",
        None,
    )


async def api_error_handler(
    request: Request,
    exc: APIError,
) -> JSONResponse:
    request_id = _request_id(request)

    content = {
        "error_code": exc.error_code,
        "message": exc.message,
        "request_id": request_id,
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={
            "X-Request-ID": request_id,
        }
        if request_id
        else {},
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    request_id = _request_id(request)

    content = {
        "error_code": "HTTP_ERROR",
        "message": (
            exc.detail
            if isinstance(exc.detail, str)
            else "HTTP request failed."
        ),
        "request_id": request_id,
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={
            "X-Request-ID": request_id,
        }
        if request_id
        else {},
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = _request_id(request)

    return JSONResponse(
        status_code=422,
        content={
            "error_code": "REQUEST_VALIDATION_ERROR",
            "message": "Request validation failed.",
            "request_id": request_id,
        },
        headers={
            "X-Request-ID": request_id,
        }
        if request_id
        else {},
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = _request_id(request)

    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred.",
            "request_id": request_id,
        },
        headers={
            "X-Request-ID": request_id,
        }
        if request_id
        else {},
    )