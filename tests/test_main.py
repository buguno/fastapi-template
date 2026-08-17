from http import HTTPStatus


def test_read_root_returns_ok_and_hello_world(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Hello World!'}
