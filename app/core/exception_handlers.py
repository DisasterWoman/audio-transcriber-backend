from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.errors import AppError


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[dict] | None = None,
) -> JSONResponse:
    error = {
        "code": code,
        "message": message,
        "request_id": get_request_id(request),
    }

    if details is not None:
        error["details"] = details

    return JSONResponse(status_code=status_code, content={"error": error})


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return error_response(
        request=request,
        status_code=exc.status_code,
        code="http_error",
        message=str(exc.detail),
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return error_response(
        request=request,
        status_code=422,
        code="validation_error",
        message="Request validation failed",
        details=jsonable_encoder(exc.errors()),
    )


async def database_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    return error_response(
        request=request,
        status_code=503,
        code="database_error",
        message="Database request failed",
    )
