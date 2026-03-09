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


async def diaspofinance_error_handler(request: Request, exc: DiaspoFinanceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
