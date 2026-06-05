"""
Regression tests for gameplay bug fixes.

Covers:
- ISSUE-002: init_defaults seeds exactly 3 player classes (not 6).
- ISSUE-007/001: monster tile content matches the persisted monster HP (single source).
- ISSUE-101: inspecting/resting on a live monster does not complete the tile.
"""
import pytest

from pq_app import create_app
from pq_app.model import db, User, Playthrough, TileTypeOption, PlayerClass, init_defaults
from pq_app.services.tile_service import TileService
from pq_app.services.combat_service import CombatService


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        init_defaults()
        yield app
        db.session.remove()
        db.drop_all()


def _player(app):
    player = User(username="bugfix_player")
    player.set_password("pw")
    db.session.add(player)
    db.session.commit()
    return player


def _monster_tile(player):
    playthrough = Playthrough(user_id=player.id)
    db.session.add(playthrough)
    db.session.flush()
    monster_type = TileTypeOption.query.filter_by(name="monster").first()
    tile = TileService().create_tile(
        user_id=player.id, playthrough_id=playthrough.id, tile_type_id=monster_type.id
    )
    db.session.add(tile)
    db.session.commit()
    return tile


def test_init_defaults_seeds_three_player_classes(app):
    """ISSUE-002: the duplicate seed loop is gone; exactly 3 classes exist."""
    with app.app_context():
        names = [c.name for c in PlayerClass.query.order_by(PlayerClass.id).all()]
        assert names == ["witch", "fighter", "healer"]


def test_monster_content_matches_persisted_hp(app):
    """ISSUE-007/001: the HP shown in tile content equals monster_max_hp."""
    with app.app_context():
        player = _player(app)
        tile = _monster_tile(player)
        assert tile.monster_max_hp is not None
        assert f"({tile.monster_max_hp} HP)" in tile.content


def test_inspect_does_not_complete_live_monster_tile(app):
    """ISSUE-101: inspecting a live monster does not complete the tile."""
    with app.app_context():
        player = _player(app)
        tile = _monster_tile(player)
        assert tile.is_monster_alive is True

        with app.test_request_context():
            result = CombatService().execute_action(
                player=player, tile=tile, action_name="inspect", tile_type_name="monster"
            )

        assert result.tile_completed is False
        assert tile.is_monster_alive is True


def test_rest_does_not_complete_live_monster_tile(app):
    """ISSUE-101: resting near a live monster hurts but does not complete the tile."""
    with app.app_context():
        player = _player(app)
        tile = _monster_tile(player)

        with app.test_request_context():
            result = CombatService().execute_action(
                player=player, tile=tile, action_name="rest", tile_type_name="monster"
            )

        assert result.tile_completed is False
        assert tile.is_monster_alive is True
