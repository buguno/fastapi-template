from dataclasses import asdict

from sqlalchemy import select

from app.models import User


def test_create_user(session, faker, mock_db_time):
    username = faker.user_name()
    password = faker.password()
    email = faker.email()

    with mock_db_time(model=User) as time:
        new_user = User(username=username, password=password, email=email)
        session.add(new_user)
        session.commit()

    user = session.scalar(select(User).where(User.username == username))

    assert asdict(user) == {
        'id': 1,
        'username': username,
        'password': password,
        'email': email,
        'created_at': time,
    }
