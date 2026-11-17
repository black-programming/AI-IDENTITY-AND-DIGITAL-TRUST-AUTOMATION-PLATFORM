"""Custom error classes and standard error envelopes."""

from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorEnvelope(BaseModel):
    success: bool = False
    error: ErrorDetail
    trace_id: Optional[str] = None


class PlatformException(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        field: Optional[str] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.field = field


class AuthenticationException(PlatformException):
    def __init__(self, message: str = "Authentication failed or token invalid"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_INVALID_TOKEN",
            message=message,
        )


class PermissionDeniedException(PlatformException):
    def __init__(self, message: str = "Insufficient permissions for requested resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTH_FORBIDDEN",
            message=message,
        )


class InvalidStateTransitionException(PlatformException):
    def __init__(self, message: str = "Invalid case state transition"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_STATE_TRANSITION",
            message=message,
        )


class ValidationException(PlatformException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_FAILED",
            message=message,
        )


class NotFoundException(PlatformException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            message=message,
        )


class CaseNotFoundException(PlatformException):
    def __init__(self, case_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="CASE_NOT_FOUND",
            message=f"Verification case {case_id} not found",
        )


class EvidenceNotFoundException(PlatformException):
    def __init__(self, file_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="EVIDENCE_NOT_FOUND",
            message=f"Evidence file '{file_id}' not found",
        )


class PayloadTooLargeException(PlatformException):
    def __init__(self, message: str = "File size exceeds maximum permitted limit (10 MB)"):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="PAYLOAD_TOO_LARGE",
            message=message,
        )


class InvalidFileSignatureException(PlatformException):
    def __init__(self, message: str = "File magic byte signature does not match declared MIME type"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_FILE_SIGNATURE",
            message=message,
        )


class ChecksumMismatchException(PlatformException):
    def __init__(self, message: str = "Client-supplied SHA-256 does not match computed file digest"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="CHECKSUM_MISMATCH",
            message=message,
        )


class QuarantineViolationException(PlatformException):
    def __init__(self, message: str = "Evidence file is in quarantine and cannot be accessed"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="QUARANTINE_VIOLATION",
            message=message,
        )


class ConflictException(PlatformException):
    def __init__(self, message: str = "Resource conflict detected"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            message=message,
        )


async def platform_exception_handler(request: Request, exc: PlatformException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorEnvelope(
            success=False,
            error=ErrorDetail(code=exc.error_code, message=str(exc.detail), field=exc.field),
            trace_id=getattr(request.state, "trace_id", None),
        ).model_dump(),
    )
