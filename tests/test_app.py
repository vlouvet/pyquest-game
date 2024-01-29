#testapp.py
import pytest
from pq_app import app as pq


@pytest.fixture()
def app():
    app = pq.create_app()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()

def test_get_play(client):
    response = client.get("/")
    assert b"<h1>PyQuest Game</h1>" in response.data

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
