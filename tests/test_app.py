from http import HTTPStatus

from fastapi.testclient import TestClient

from app.app import app

client = TestClient(app)


def test_root_return_ok_and_hello_world():
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Hello World!'}
