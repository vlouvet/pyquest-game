#testapp.py
import pytest
from app import create_app

@pytest.fixture()
def app():
    app = create_app()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()

def test_get_play(client):
    response = client.get("/play")
    assert b"<h1>PyQuest Game</h1>" in response.data

def test_post_play(client):
    post_data = {'form':{'name':'test'}}
    response = client.post("/play", data=post_data)
    assert b"<h2>Character setup</h2>" in response.data

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
