from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.core.exceptions import DomainError, EmptyFile, FileNotFound, StoredFileMissing

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    FileNotFound: status.HTTP_404_NOT_FOUND,
    StoredFileMissing: status.HTTP_404_NOT_FOUND,
    EmptyFile: status.HTTP_400_BAD_REQUEST,
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
        code = _STATUS_BY_ERROR.get(type(error), status.HTTP_500_INTERNAL_SERVER_ERROR)
        return JSONResponse(status_code=code, content={"detail": error.detail})
