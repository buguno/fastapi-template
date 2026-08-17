from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import InvalidCredentials
from app.models.user import User
from app.security import create_access_token, verify_password


def authenticate(session: Session, email: str, password: str) -> str:
    user = session.scalar(select(User).where(User.email == email))

    if not user or not verify_password(password, user.password):
        raise InvalidCredentials('Incorrect email or password')

    return create_access_token(data={'sub': user.email})
