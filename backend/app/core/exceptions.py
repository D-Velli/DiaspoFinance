from fastapi import Request
from fastapi.responses import JSONResponse


class DiaspoFinanceError(Exception):
    default_code: str = "INTERNAL_ERROR"
    default_status_code: int = 500
    default_message: str = "An internal error occurred"

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ):
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status_code
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(DiaspoFinanceError):
    default_code = "NOT_FOUND"
    default_status_code = 404
    default_message = "Resource not found"


class ValidationError(DiaspoFinanceError):
    default_code = "VALIDATION_ERROR"
    default_status_code = 422
    default_message = "Validation failed"


class ForbiddenError(DiaspoFinanceError):
    default_code = "FORBIDDEN"
    default_status_code = 403
    default_message = "You do not have permission to perform this action"


class TontineFullError(DiaspoFinanceError):
    default_code = "TONTINE_FULL"
    default_status_code = 400
    default_message = "This tontine has reached its maximum capacity"


class PlafondExceededError(DiaspoFinanceError):
    default_code = "PLAFOND_EXCEEDED"
    default_status_code = 400
    default_message = "Regulatory ceiling exceeded"


class InvalidHandsError(DiaspoFinanceError):
    default_code = "INVALID_HANDS"
    default_status_code = 400
    default_message = "Hands must be 0.5, 1, or 2"


class TontineNotDraftError(DiaspoFinanceError):
    default_code = "TONTINE_NOT_DRAFT"
    default_status_code = 400
    default_message = "This action is only allowed on draft tontines"


class RateLimitError(DiaspoFinanceError):
    default_code = "RATE_LIMIT_EXCEEDED"
    default_status_code = 429
    default_message = "Too many requests"


async def diaspofinance_error_handler(request: Request, exc: DiaspoFinanceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    import structlog

    logger = structlog.get_logger()
    logger.error("unhandled_exception", exc_type=type(exc).__name__, detail=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred"}},
    )
