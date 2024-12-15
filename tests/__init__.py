import pytest
from pq_app import app, db

@pytest.fixture
def test_app():
    """Set up the Flask app for testing."""
    app2 = app.create_app()
    with app2.app_context():
        db.create_all()  # Create tables
        yield app2
        db.session.remove()
        db.drop_all()  # Clean up the database after tests

@pytest.fixture
def client(test_app):
    """Provide a test client for Flask app."""
    return test_app.client()

@pytest.fixture
def authenticated_client(client):
    """Log in a test user and return the authenticated client."""
    client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    return client
