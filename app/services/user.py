from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    NotEnoughPermissions,
    UserAlreadyExists,
    UserNotFound,
)
from app.models.user import User
from app.schemas.filters import FilterPage
from app.schemas.user import UserSchema
from app.security import get_password_hash


async def create_user(session: AsyncSession, data: UserSchema) -> User:
    db_user = await session.scalar(
        select(User).where(
            (User.username == data.username) | (User.email == data.email)
        )
    )

    if db_user:
        if db_user.username == data.username:
            raise UserAlreadyExists('Username already exists')
        raise UserAlreadyExists('Email already exists')

    db_user = User(
        username=data.username,
        password=get_password_hash(data.password),
        email=data.email,
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user


async def list_users(session: AsyncSession, filters: FilterPage) -> list[User]:
    query = await session.scalars(
        select(User).offset(filters.offset).limit(filters.limit)
    )
    users = query.all()

    return list(users)


async def update_user(
    session: AsyncSession, user_id: int, data: UserSchema, current_user: User
) -> User:
    if current_user.id != user_id:
        raise NotEnoughPermissions('Not enough permissions')

    db_user = await session.scalar(select(User).where(User.id == user_id))

    if not db_user:
        raise UserNotFound('User not found')

    try:
        db_user.username = data.username
        db_user.password = get_password_hash(data.password)
        db_user.email = data.email
        await session.commit()
        await session.refresh(db_user)

    except IntegrityError:
        await session.rollback()
        raise UserAlreadyExists('Username or Email already exists')

    return db_user


async def delete_user(
    session: AsyncSession, user_id: int, current_user: User
) -> None:
    if current_user.id != user_id:
        raise NotEnoughPermissions('Not enough permissions')

    db_user = await session.scalar(select(User).where(User.id == user_id))

    if not db_user:
        raise UserNotFound('User not found')

    await session.delete(db_user)
    await session.commit()
