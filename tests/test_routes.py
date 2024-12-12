# # tests/test_routes.py
# from pq_app import app
# from config import TestingConfig

# import pytest
import pytest
from werkzeug.security import generate_password_hash
from pq_app import create_app, db
from pq_app.model import User


def test_home_redirect(client):
    """Test that the home route redirects to login for unauthenticated users."""
    response = client.get('/')
    assert response.status_code == 302  # HTTP status for redirect
    assert b'/login?next=%2F' in response.data



@pytest.fixture
def setup_test_user(client):
    """Fixture to add a test user to the database."""
    with client.application.app_context():
        user = User(username="testuser", password_hash=generate_password_hash("testpassword"))
        db.session.add(user)
        db.session.commit()

def test_login_get(client):
    """Test the GET request to the login route."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data  # Verify "Login" appears in the rendered template

def test_login_post_success(client, setup_test_user):
    """Test a successful POST login."""
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "testpassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'<input type="submit" value="Play">' in response.data  # Replace with the expected greeting message

def test_login_post_failure(client):
    """Test a failed POST login."""
    response = client.post(
        "/login",
        data={"username": "invaliduser", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Login' in response.data
