import pytest

from app.exceptions import (
    NotEnoughPermissions,
    UserAlreadyExists,
    UserNotFound,
)
from app.models.user import User
from app.schemas.user import UserSchema
from app.services import user as user_service


@pytest.fixture
def other_user(faker):
    """Unpersisted user, to simulate an id that does not exist."""
    stranger = User(
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
    )
    stranger.id = 999

    return stranger


@pytest.mark.asyncio
async def test_create_user_with_taken_username(session, user, faker):
    data = UserSchema(
        username=user.username, email=faker.email(), password=faker.password()
    )

    with pytest.raises(UserAlreadyExists, match='Username already exists'):
        await user_service.create_user(session, data)


@pytest.mark.asyncio
async def test_create_user_with_taken_email(session, user, faker):
    data = UserSchema(
        username=faker.user_name(), email=user.email, password=faker.password()
    )

    with pytest.raises(UserAlreadyExists, match='Email already exists'):
        await user_service.create_user(session, data)


@pytest.mark.asyncio
async def test_update_user_from_another_user(session, user, faker):
    data = UserSchema(
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
    )

    with pytest.raises(NotEnoughPermissions, match='Not enough permissions'):
        await user_service.update_user(session, user.id + 1, data, user)


@pytest.mark.asyncio
async def test_update_user_that_does_not_exist(session, other_user, faker):
    data = UserSchema(
        username=faker.user_name(),
        email=faker.email(),
        password=faker.password(),
    )

    with pytest.raises(UserNotFound, match='User not found'):
        await user_service.update_user(
            session, other_user.id, data, other_user
        )


@pytest.mark.asyncio
async def test_delete_user_from_another_user(session, user):
    with pytest.raises(NotEnoughPermissions, match='Not enough permissions'):
        await user_service.delete_user(session, user.id + 1, user)


@pytest.mark.asyncio
async def test_delete_user_that_does_not_exist(session, other_user):
    with pytest.raises(UserNotFound, match='User not found'):
        await user_service.delete_user(session, other_user.id, other_user)
