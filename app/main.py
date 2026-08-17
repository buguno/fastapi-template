from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    DomainError,
    InvalidCredentials,
    NotEnoughPermissions,
    UserAlreadyExists,
    UserNotFound,
)
from app.routers import auth, users
from app.schemas.message import Message
from app.settings import settings

app = FastAPI(
    docs_url=None if settings.is_production else '/docs',
    redoc_url=None if settings.is_production else '/redoc',
)

STATUS_BY_ERROR = {
    UserAlreadyExists: HTTPStatus.CONFLICT,
    UserNotFound: HTTPStatus.NOT_FOUND,
    NotEnoughPermissions: HTTPStatus.FORBIDDEN,
    InvalidCredentials: HTTPStatus.UNAUTHORIZED,
}


@app.exception_handler(DomainError)
def domain_error_handler(request: Request, exc: DomainError):
    status = STATUS_BY_ERROR.get(type(exc), HTTPStatus.BAD_REQUEST)
    return JSONResponse(status_code=status, content={'detail': str(exc)})


app.include_router(users.router)
app.include_router(auth.router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Hello World!'}
