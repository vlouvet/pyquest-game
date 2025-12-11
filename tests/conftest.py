import pytest
from pq_app import create_app
from pq_app.model import db



@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app("testing")
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def authenticated_client(client, app):
    """Create an authenticated test client."""
    with app.app_context():
        from pq_app.model import User

        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()

    client.post("/login", data={"username": "testuser", "password": "testpass"})
    return client
