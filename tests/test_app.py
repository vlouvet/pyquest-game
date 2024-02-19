#testapp.py
import pytest
from pq_app import app as pq
from bs4 import BeautifulSoup

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

def test_post_play(client):
    # Get the CSRF token
    response = client.get("/")
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.find(id='csrf_token')['value']
    # Include the CSRF token in the POST request
    response = client.post("/", data={"username": "l2@v1.c", "csrf_token": csrf_token})
    postSoup = BeautifulSoup(response.data, 'html.parser')
    h2 = postSoup.find('h2')
    #assert the response has no messages
    assert "Welcome Traveler" not in h2.text

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
