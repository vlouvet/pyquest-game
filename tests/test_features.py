"""
Tests for new gameplay features.

- FEATURE-001: XP & leveling (award_xp, level-up HP growth, XP on monster defeat).
- FEATURE-004: defense stance (persisted) and working flee.
"""
import pytest

from pq_app import create_app
from pq_app.model import db, User, Playthrough, TileTypeOption, CombatAction, init_defaults
from pq_app.services.tile_service import TileService
from pq_app.services.combat_service import CombatService
from pq_app.services.player_service import PlayerService


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        init_defaults()
        yield app
        db.session.remove()
        db.drop_all()


def _player(level=1, exp=0, max_hp=100, hp=100):
    player = User(username="feat_player")
    player.set_password("pw")
    db.session.add(player)
    db.session.commit()
    player.level = level
    player.exp_points = exp
    player.max_hp = max_hp
    player.hitpoints = hp
    db.session.commit()
    return player


def _monster_tile(player):
    pt = Playthrough(user_id=player.id)
    db.session.add(pt)
    db.session.flush()
    mtype = TileTypeOption.query.filter_by(name="monster").first()
    tile = TileService().create_tile(user_id=player.id, playthrough_id=pt.id, tile_type_id=mtype.id)
    db.session.add(tile)
    db.session.commit()
    return tile


# ----------------------------- FEATURE-001 -----------------------------

def test_award_xp_no_levelup_below_threshold(app):
    with app.app_context():
        player = _player()
        result = PlayerService().award_xp(player, 50)  # XP_BASE=100
        assert result["leveled_up"] is False
        assert player.level == 1
        assert player.exp_points == 50


def test_award_xp_levels_up_and_grows_hp(app):
    with app.app_context():
        player = _player(max_hp=100, hp=80)
        result = PlayerService().award_xp(player, 100)  # exactly enough for L1->L2
        assert result["leveled_up"] is True
        assert player.level == 2
        assert player.max_hp == 110          # +HP_PER_LEVEL (10)
        assert player.hitpoints == 90        # healed by the gained HP
        assert player.exp_points == 0        # progress reset after level up


def test_award_xp_multiple_levels_in_one_award(app):
    with app.app_context():
        player = _player()
        # L1->2 needs 100, L2->3 needs 150 => 250 grants two levels exactly.
        result = PlayerService().award_xp(player, 250)
        assert player.level == 3
        assert result["levels_gained"] == 2
        assert player.exp_points == 0


def test_monster_defeat_awards_xp(app):
    with app.app_context():
        player = _player()
        tile = _monster_tile(player)
        heavy = CombatAction.query.filter_by(code="attack_heavy").first()
        with app.test_request_context():
            while tile.is_monster_alive:
                CombatService().execute_combat_action(player=player, tile=tile, combat_action=heavy)
        # Defeating the monster should have granted XP (level up and/or exp_points progress).
        assert player.level > 1 or player.exp_points > 0


# ----------------------------- FEATURE-004 -----------------------------

def test_defend_queues_defense(app):
    with app.app_context():
        player = _player()
        tile = _monster_tile(player)
        defend = CombatAction.query.filter_by(code="defend").first()
        with app.test_request_context():
            CombatService().execute_combat_action(player=player, tile=tile, combat_action=defend)
        assert tile.player_defense_pending == defend.defense_boost


def test_defense_reduces_counter_attack(app):
    with app.app_context():
        # Deterministic counter-attack: always happens, always 10 damage.
        app.config["COUNTER_ATTACK_CHANCE"] = 100
        app.config["COUNTER_DAMAGE_MIN"] = 10
        app.config["COUNTER_DAMAGE_MAX"] = 10
        player = _player(hp=100, max_hp=100)
        tile = _monster_tile(player)
        tile.monster_current_hp = 100
        tile.monster_max_hp = 100
        tile.player_defense_pending = 4
        db.session.commit()

        light = CombatAction.query.filter_by(code="attack_light").first()
        light.success_rate = 100  # guarantee the attack lands so the counter triggers
        with app.test_request_context():
            CombatService().execute_combat_action(player=player, tile=tile, combat_action=light)

        # 10 incoming - 4 defense = 6 damage taken; defense consumed.
        assert player.hitpoints == 94
        assert tile.player_defense_pending is None


def test_flee_success_ends_encounter(app):
    with app.app_context():
        player = _player()
        tile = _monster_tile(player)
        flee = CombatAction.query.filter_by(code="flee").first()
        flee.success_rate = 100
        with app.test_request_context():
            result = CombatService().execute_combat_action(player=player, tile=tile, combat_action=flee)
        assert result.success is True
        assert result.tile_completed is True
        assert player.hitpoints == 100  # no damage on a clean escape


def test_flee_failure_keeps_encounter_and_damages(app):
    with app.app_context():
        app.config["COUNTER_DAMAGE_MIN"] = 8
        app.config["COUNTER_DAMAGE_MAX"] = 8
        player = _player()
        tile = _monster_tile(player)
        flee = CombatAction.query.filter_by(code="flee").first()
        flee.success_rate = 0  # guarantee failure
        with app.test_request_context():
            result = CombatService().execute_combat_action(player=player, tile=tile, combat_action=flee)
        assert result.success is False
        assert result.tile_completed is False
        assert player.hitpoints == 92  # took the 8-damage free hit
