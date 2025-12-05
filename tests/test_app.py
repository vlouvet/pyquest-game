# test_app.py
import pytest
from pq_app import create_app
from bs4 import BeautifulSoup
from flask import url_for
from pq_app.model import db, User, Tile, TileTypeOption


@pytest.fixture()
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


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def init_database(app):
    with app.app_context():
        user = User(username="testuser")
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()
        tile_type = TileTypeOption(name="test_tile")
        db.session.add(tile_type)
        db.session.commit()
        tile = Tile(user_id=user.id, type=tile_type.id)
        db.session.add(tile)
        db.session.commit()
        yield db


def test_get_play(client):
    """Test that the home route requires authentication."""
    response = client.get("/")
    # Should redirect to login since user is not authenticated
    assert response.status_code == 302
    assert b"/login" in response.data or "/login" in response.location


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
