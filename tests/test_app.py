# testapp.py
import pytest
from pq_app import create_app
from pq_app.model import db, User, Tile, TileTypeOption


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
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
        user.set_password("testpassword")  # hashes and sets password_hash
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
    response = client.get("/")
    assert response.data is not None


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
