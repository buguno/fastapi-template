from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import InvalidCredentials
from app.models.user import User
from app.security import create_access_token, verify_password


async def authenticate(
    session: AsyncSession, email: str, password: str
) -> str:
    user = await session.scalar(select(User).where(User.email == email))

    if not user or not verify_password(password, user.password):
        raise InvalidCredentials('Incorrect email or password')

    return create_access_token(data={'sub': user.email})


def refresh(user: User) -> str:
    return create_access_token(data={'sub': user.email})
