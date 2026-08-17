from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.database import DbSession
from app.schemas.token import Token
from app.security import CurrentUser
from app.services import auth as auth_service

router = APIRouter(prefix='/auth', tags=['auth'])

OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2Form, session: DbSession):
    access_token = await auth_service.authenticate(
        session, form_data.username, form_data.password
    )

    return {'access_token': access_token, 'token_type': 'bearer'}


@router.post('/refresh', response_model=Token)
async def refresh_access_token(current_user: CurrentUser):
    access_token = auth_service.refresh(current_user)

    return {'access_token': access_token, 'token_type': 'bearer'}
