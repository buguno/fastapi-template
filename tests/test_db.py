from faker import Faker
from sqlalchemy import select

from app.models import User

faker = Faker()


def test_create_user(session):
    username = faker.user_name()
    password = faker.password()
    email = faker.email()

    new_user = User(username=username, password=password, email=email)
    session.add(new_user)
    session.commit()

    user = session.scalar(select(User).where(User.username == username))

    assert user.username == username
