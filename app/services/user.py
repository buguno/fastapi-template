from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import (
    NotEnoughPermissions,
    UserAlreadyExists,
    UserNotFound,
)
from app.models.user import User
from app.schemas.filters import FilterPage
from app.schemas.user import UserSchema
from app.security import get_password_hash


def create_user(session: Session, data: UserSchema) -> User:
    db_user = session.scalar(
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
    session.commit()
    session.refresh(db_user)

    return db_user


def list_users(session: Session, filters: FilterPage) -> list[User]:
    users = list(
        session.scalars(
            select(User).offset(filters.offset).limit(filters.limit)
        ).all()
    )
    return users


def update_user(
    session: Session, user_id: int, data: UserSchema, current_user: User
) -> User:
    if current_user.id != user_id:
        raise NotEnoughPermissions('Not enough permissions')

    db_user = session.scalar(select(User).where(User.id == user_id))

    if not db_user:
        raise UserNotFound('User not found')

    try:
        db_user.username = data.username
        db_user.password = get_password_hash(data.password)
        db_user.email = data.email
        session.commit()
        session.refresh(db_user)

    except IntegrityError:
        raise UserAlreadyExists('Username or Email already exists')

    return db_user


def delete_user(session: Session, user_id: int, current_user: User) -> None:
    if current_user.id != user_id:
        raise NotEnoughPermissions('Not enough permissions')

    db_user = session.scalar(select(User).where(User.id == user_id))

    if not db_user:
        raise UserNotFound('User not found')

    session.delete(db_user)
    session.commit()
