#testapp.py
import pytest, flask
from flask_wtf.csrf import generate_csrf
from flask.testing import FlaskClient as BaseFlaskClient
from pq_app import app as pq_app


@pytest.fixture()
def app():
    app = pq_app.create_app()
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
