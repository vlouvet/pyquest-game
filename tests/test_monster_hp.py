"""
Test Monster HP Persistence

Tests for the persistent monster HP system where monsters retain HP across multiple attacks.
"""

import pytest
from pq_app import create_app
from pq_app.model import db, User, Tile, Playthrough, CombatAction, TileTypeOption
from pq_app.services.combat_service import CombatService
from pq_app.services.tile_service import TileService


@pytest.fixture
def app():
    """Create test app"""
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        # Create test data
        from pq_app.model import init_defaults
        init_defaults()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def test_player(app):
    """Create a test player"""
    with app.app_context():
        player = User(username="testplayer", email="test@example.com")
        player.set_password("testpass")
        player.hit_points = 100
        player.max_hit_points = 100
        player.gold = 50
        db.session.add(player)
        db.session.commit()
        return player.id


class TestMonsterHPPersistence:
    """Test monster HP persistence across combat actions"""

    def test_monster_tile_has_hp(self, app, test_player):
        """Test that monster tiles are created with HP"""
        with app.app_context():
            player = db.session.get(User, test_player)
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()

            # Create a monster tile using tile service
            tile_service = TileService()
            monster_type = TileTypeOption.query.filter_by(name="monster").first()
            
            tile = tile_service.create_tile(
                user_id=player.id,
                playthrough_id=playthrough.id,
                tile_type_id=monster_type.id
            )
            db.session.add(tile)
            db.session.commit()
            
            # Verify monster has HP
            assert tile.monster_current_hp is not None
            assert tile.monster_max_hp is not None
            assert tile.monster_current_hp == tile.monster_max_hp
            assert 30 <= tile.monster_current_hp <= 70
            assert tile.is_monster_alive is True

    def test_monster_hp_decreases_on_attack(self, app, test_player):
        """Test that monster HP decreases when attacked"""
        with app.app_context():
            player = db.session.get(User, test_player)
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()

            # Create a monster tile
            tile_service = TileService()
            monster_type = TileTypeOption.query.filter_by(name="monster").first()
            tile = tile_service.create_tile(
                user_id=player.id,
                playthrough_id=playthrough.id,
                tile_type_id=monster_type.id
            )
            db.session.add(tile)
            db.session.commit()
            
            initial_hp = tile.monster_current_hp

            # Execute attack
            combat_service = CombatService()
            combat_action = CombatAction.query.filter_by(code="attack_light").first()
            
            with app.test_request_context():
                result = combat_service.execute_combat_action(
                    player=player,
                    tile=tile,
                    combat_action=combat_action
                )
            
            # Verify HP decreased
            assert tile.monster_current_hp < initial_hp
            # Monster should still be alive after one light attack
            assert tile.is_monster_alive is True

    def test_multiple_attacks_accumulate_damage(self, app, test_player):
        """Test that multiple attacks progressively reduce monster HP"""
        with app.app_context():
            player = db.session.get(User, test_player)
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()

            # Create a monster tile with low HP for testing
            tile_service = TileService()
            monster_type = TileTypeOption.query.filter_by(name="monster").first()
            tile = tile_service.create_tile(
                user_id=player.id,
                playthrough_id=playthrough.id,
                tile_type_id=monster_type.id
            )
            db.session.add(tile)
            db.session.commit()
            
            # Manually set low HP for testing
            tile.monster_current_hp = 20
            tile.monster_max_hp = 20
            db.session.commit()

            combat_service = CombatService()
            combat_action = CombatAction.query.filter_by(code="attack_heavy").first()
            hp_values = [tile.monster_current_hp]

            # Attack multiple times until monster is defeated
            with app.test_request_context():
                for i in range(10):  # Increased to ensure monster is defeated
                    result = combat_service.execute_combat_action(
                        player=player,
                        tile=tile,
                        combat_action=combat_action
                    )
                    hp_values.append(tile.monster_current_hp)
                    
                    # Stop if monster is defeated
                    if not tile.is_monster_alive:
                        break

            # Verify HP never increased and eventually reached 0 or below
            for i in range(len(hp_values) - 1):
                # HP should never increase
                assert hp_values[i] >= hp_values[i + 1]
            
            # Monster should be defeated after enough attacks
            assert hp_values[-1] <= 0

    def test_monster_defeat_completes_tile(self, app, test_player):
        """Test that defeating a monster marks tile as completed"""
        with app.app_context():
            player = db.session.get(User, test_player)
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()

            # Create a monster tile with very low HP
            tile_service = TileService()
            monster_type = TileTypeOption.query.filter_by(name="monster").first()
            tile = tile_service.create_tile(
                user_id=player.id,
                playthrough_id=playthrough.id,
                tile_type_id=monster_type.id
            )
            db.session.add(tile)
            db.session.commit()
            
            # Set HP to 1 so next attack will kill it
            tile.monster_current_hp = 1
            tile.monster_max_hp = 50
            db.session.commit()

            combat_service = CombatService()
            combat_action = CombatAction.query.filter_by(code="attack_heavy").first()
            
            with app.test_request_context():
                result = combat_service.execute_combat_action(
                    player=player,
                    tile=tile,
                    combat_action=combat_action
                )

            # Verify monster is defeated
            assert tile.monster_current_hp <= 0
            assert tile.is_monster_alive is False
            assert result.tile_completed is True

    def test_monster_not_completed_if_alive(self, app, test_player):
        """Test that tile is not completed if monster still has HP"""
        with app.app_context():
            player = db.session.get(User, test_player)
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()

            # Create a monster tile
            tile_service = TileService()
            monster_type = TileTypeOption.query.filter_by(name="monster").first()
            tile = tile_service.create_tile(
                user_id=player.id,
                playthrough_id=playthrough.id,
                tile_type_id=monster_type.id
            )
            db.session.add(tile)
            db.session.commit()

            combat_service = CombatService()
            combat_action = CombatAction.query.filter_by(code="attack_light").first()
            
            with app.test_request_context():
                result = combat_service.execute_combat_action(
                    player=player,
                    tile=tile,
                    combat_action=combat_action
                )

            # Verify tile is not completed if monster is alive
            if tile.is_monster_alive:
                assert result.tile_completed is False

    def test_monster_hp_percent_calculation(self, app, test_player):
        """Test that monster HP percentage is calculated correctly"""
        with app.app_context():
            player = db.session.get(User, test_player)
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()

            # Create a monster tile
            tile_service = TileService()
            monster_type = TileTypeOption.query.filter_by(name="monster").first()
            tile = tile_service.create_tile(
                user_id=player.id,
                playthrough_id=playthrough.id,
                tile_type_id=monster_type.id
            )
            db.session.add(tile)
            db.session.commit()
            
            # Set specific HP values
            tile.monster_max_hp = 100
            tile.monster_current_hp = 50
            db.session.commit()

            # Verify HP percentage
            assert tile.monster_hp_percent == 0.5

            # Reduce HP
            tile.monster_current_hp = 25
            db.session.commit()
            assert tile.monster_hp_percent == 0.25

            # HP at 0
            tile.monster_current_hp = 0
            db.session.commit()
            assert tile.monster_hp_percent == 0.0

    def test_non_monster_tiles_have_no_hp(self, app, test_player):
        """Test that non-monster tiles don't have HP values"""
        with app.app_context():
            player = db.session.get(User, test_player)
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()

            # Create a non-monster tile (treasure)
            tile_service = TileService()
            treasure_type = TileTypeOption.query.filter_by(name="treasure").first()
            
            tile = tile_service.create_tile(
                user_id=player.id,
                playthrough_id=playthrough.id,
                tile_type_id=treasure_type.id
            )
            db.session.add(tile)
            db.session.commit()

            # Verify no HP
            assert tile.monster_current_hp is None
            assert tile.monster_max_hp is None
