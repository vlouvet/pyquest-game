import pytest
from pq_app import create_app, db

@pytest.fixture
def client():
    app = create_app()
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        # with app.app_context():
        #     db.drop_all()

@pytest.fixture
def authenticated_client(client):
    with client.application.app_context():
        from pq_app.model import User
        user = User(username="testuser", password_hash="testpass")
        db.session.add(user)
        db.session.commit()

    client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    return client