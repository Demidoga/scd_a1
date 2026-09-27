"""Application-level exceptions + the handlers that turn them into the
API's error envelope. Registered once in app/main.py — not per-route.

FastAPI's default for a Pydantic validation failure is 422; the assignment
contract requires 400 (docs/architecture/backend.md §5), so
RequestValidationError gets its own handler here too.
"""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.enums import Status as ComplaintStatus
from app.domain.schemas import ErrorResponse, FieldError


class ComplaintNotFoundError(Exception):
    def __init__(self, complaint_id: object) -> None:
        self.complaint_id = complaint_id
        super().__init__(f"Complaint {complaint_id} not found")


class InvalidTransitionError(Exception):
    def __init__(self, current: ComplaintStatus, target: ComplaintStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition complaint from {current.value} to {target.value}")


class RateLimitExceededError(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Rate limit exceeded")


class DependencyUnavailableError(Exception):
    def __init__(self, dependency: str) -> None:
        self.dependency = dependency
        super().__init__(f"{dependency} is unavailable")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            FieldError(
                field=".".join(str(p) for p in err["loc"] if p != "body"),
                message=err["msg"],
            )
            for err in exc.errors()
        ]
        body = ErrorResponse(detail="Validation failed", errors=errors)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder(body),
        )

    @app.exception_handler(ComplaintNotFoundError)
    async def handle_not_found(request: Request, exc: ComplaintNotFoundError) -> JSONResponse:
        body = ErrorResponse(detail=str(exc))
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(body))

    @app.exception_handler(InvalidTransitionError)
    async def handle_invalid_transition(
        request: Request, exc: InvalidTransitionError
    ) -> JSONResponse:
        body = ErrorResponse(
            detail=f"Invalid status transition: {exc.current.value} -> {exc.target.value}"
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=jsonable_encoder(body))

    @app.exception_handler(RateLimitExceededError)
    async def handle_rate_limit(request: Request, exc: RateLimitExceededError) -> JSONResponse:
        body = ErrorResponse(detail="Too many requests")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=jsonable_encoder(body),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        )

    @app.exception_handler(DependencyUnavailableError)
    async def handle_dependency_unavailable(
        request: Request, exc: DependencyUnavailableError
    ) -> JSONResponse:
        body = ErrorResponse(detail=f"{exc.dependency} is unavailable")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=jsonable_encoder(body)
        )
