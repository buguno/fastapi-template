from http import HTTPStatus


def test_root_return_ok_and_hello_world(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Hello World!'}


def test_create_user(client, faker):
    username = faker.user_name()
    email = faker.email()
    password = faker.password()

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
        'id': 1,
        'username': username,
        'email': email,
    }
