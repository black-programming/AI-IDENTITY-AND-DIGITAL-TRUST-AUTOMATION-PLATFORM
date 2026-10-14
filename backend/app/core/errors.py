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


class CaseNotFoundException(PlatformException):
    def __init__(self, case_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="CASE_NOT_FOUND",
            message=f"Verification case {case_id} not found",
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
