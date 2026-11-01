"""Maps the domain errors and request validation errors to status codes and one error body."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import InvalidTitle, TodoError, TodoNotFound

STATUS_BY_ERROR: dict[type[TodoError], int] = {
    TodoNotFound: status.HTTP_404_NOT_FOUND,
    InvalidTitle: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def register_error_handlers(app: FastAPI) -> None:
    # The decorator form takes handlers typed with their own error class.
    for error_type in STATUS_BY_ERROR:
        app.exception_handler(error_type)(_handle_domain_error)
    app.exception_handler(RequestValidationError)(_handle_validation_error)


def _error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def _handle_domain_error(_: Request, error: TodoError) -> JSONResponse:
    return _error_response(STATUS_BY_ERROR[type(error)], str(error))


async def _handle_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    first = error.errors()[0]
    location = ".".join(str(part) for part in first["loc"])
    return _error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, f"{location}: {first['msg']}")
