from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.utils.exceptions import MeteoAPIException, ValidationError, AuthenticationError, ConflictError

def add_exception_handlers(app: FastAPI):
    """Add custom exception handlers to FastAPI app"""

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": exc.message}
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"error": exc.message}
        )

    @app.exception_handler(ConflictError)
    async def conflict_error_handler(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=409,
            content={"error": exc.message}
        )

    @app.exception_handler(MeteoAPIException)
    async def meteo_api_error_handler(request: Request, exc: MeteoAPIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message}
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": "Внутренняя ошибка сервера"}
        )