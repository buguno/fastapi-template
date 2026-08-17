from http import HTTPStatus

import pytest

from app.schemas.user import UserPublic


def test_create_user(client, faker):
    username = faker.user_name()
    password = faker.password()
    email = faker.email()

    response = client.post(
        '/users',
        json={
            'username': username,
            'email': email,
            'password': password,
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'username': username,
        'email': email,
        'id': 1,
    }


def test_read_users_with_users(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get('/users/')
    assert response.json() == {'users': [user_schema]}


def test_read_users_with_pagination(client, users):
    response = client.get('/users/?offset=1&limit=2')

    assert response.status_code == HTTPStatus.OK
    assert [item['id'] for item in response.json()['users']] == [
        users[1].id,
        users[2].id,
    ]


@pytest.mark.parametrize(
    'query', ['offset=-1', 'limit=0', 'limit=101', 'limit=abc']
)
def test_read_users_with_invalid_pagination(client, query):
    response = client.get(f'/users/?{query}')

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT


def test_update_user(client, user, token, faker):
    username = faker.user_name()
    email = faker.email()
    password = faker.password()

    response = client.put(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': username,
            'email': email,
            'password': password,
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': username,
        'email': email,
        'id': user.id,
    }


def test_update_integrity_error(client, user, token, faker):
    username = faker.user_name()
    email = faker.email()
    password = faker.password()

    client.post(
        '/users',
        json={
            'username': username,
            'email': email,
            'password': password,
        },
    )

    response_update = client.put(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': username,
            'email': user.email,
            'password': password,
        },
    )

    assert response_update.status_code == HTTPStatus.CONFLICT
    assert response_update.json() == {
        'detail': 'Username or Email already exists'
    }


def test_delete_user(client, user, token):
    response = client.delete(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}
