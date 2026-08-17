from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Query

from app.database import DbSession
from app.schemas.filters import FilterPage
from app.schemas.message import Message
from app.schemas.user import UserList, UserPublic, UserSchema
from app.security import CurrentUser
from app.services import user as user_service

router = APIRouter(prefix='/users', tags=['users'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
async def create_user(data: UserSchema, session: DbSession):
    new_user = await user_service.create_user(session, data)
    return new_user


@router.get('/', response_model=UserList)
async def read_users(
    session: DbSession, filters: Annotated[FilterPage, Query()]
):
    users = await user_service.list_users(session, filters)
    return {'users': users}


@router.put('/{user_id}', response_model=UserPublic)
async def update_user(
    user_id: int,
    data: UserSchema,
    session: DbSession,
    current_user: CurrentUser,
):
    updated_user = await user_service.update_user(
        session, user_id, data, current_user
    )
    return updated_user


@router.delete('/{user_id}', response_model=Message)
async def delete_user(
    user_id: int,
    session: DbSession,
    current_user: CurrentUser,
):
    await user_service.delete_user(session, user_id, current_user)
    return {'message': 'User deleted'}
