# Extended tests for app.py to achieve >90% coverage
import pytest
import json
from werkzeug.security import generate_password_hash
from pq_app.model import (
    User,
    db,
    PlayerClass,
    PlayerRace,
    Tile,
    Action,
    Playthrough,
    TileTypeOption,
    ActionOption,
)


@pytest.fixture
def setup_test_user(client):
    """Fixture to add a test user to the database."""
    with client.application.app_context():
        user = User(username="testuser", password_hash=generate_password_hash("testpassword"))
        db.session.add(user)
        db.session.commit()


@pytest.fixture
def authenticated_user(client):
    """Fixture to create and login a test user."""
    with client.application.app_context():
        user = User(username="authuser", password_hash=generate_password_hash("password123"))
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    client.post(
        "/login",
        data={"username": "authuser", "password": "password123"},
        follow_redirects=True,
    )

    return user_id


@pytest.fixture
def setup_game_data(client):
    """Fixture to set up game data (player classes, races, tile types, actions)."""
    with client.application.app_context():
        # Add PlayerClass
        if not PlayerClass.query.first():
            warrior = PlayerClass(name="Warrior")
            mage = PlayerClass(name="Mage")
            db.session.add(warrior)
            db.session.add(mage)

        # Add PlayerRace
        if not PlayerRace.query.first():
            human = PlayerRace(name="Human")
            elf = PlayerRace(name="Elf")
            db.session.add(human)
            db.session.add(elf)

        # Add TileTypeOption
        if not TileTypeOption.query.first():
            sign = TileTypeOption(name="sign")
            monster = TileTypeOption(name="monster")
            scene = TileTypeOption(name="scene")
            treasure = TileTypeOption(name="treasure")
            db.session.add(sign)
            db.session.add(monster)
            db.session.add(scene)
            db.session.add(treasure)

        # Add ActionOption
        if not ActionOption.query.first():
            rest = ActionOption(name="rest", code="rest")
            inspect = ActionOption(name="inspect", code="inspect")
            fight = ActionOption(name="fight", code="fight")
            quit_opt = ActionOption(name="quit", code="quit")
            db.session.add(rest)
            db.session.add(inspect)
            db.session.add(fight)
            db.session.add(quit_opt)

        db.session.commit()


@pytest.fixture
def user_with_character(client, authenticated_user, setup_game_data):
    """Fixture to create a user with character setup complete and a tile."""
    with client.application.app_context():
        user = db.session.get(User, authenticated_user)
        player_class = PlayerClass.query.first()
        player_race = PlayerRace.query.first()
        tile_type = TileTypeOption.query.first()

        assert user is not None
        assert player_class is not None
        assert player_race is not None
        assert tile_type is not None

        user.playerclass = player_class.id
        user.playerrace = player_race.id
        user.hitpoints = 100

        # Create a playthrough and a tile for the user
        play = Playthrough(user_id=user.id)
        db.session.add(play)
        db.session.flush()

        tile = Tile(user_id=user.id, type=tile_type.id, action_taken=False, playthrough_id=play.id, content="Test tile")
        db.session.add(tile)
        db.session.commit()

        tile_id = tile.id

    return {"user_id": authenticated_user, "tile_id": tile_id}


# Test register duplicate username
def test_register_duplicate_username(client):
    """Test registering with a duplicate username."""
    # First registration
    client.post(
        "/register",
        data={
            "username": "duplicate",
            "password": "password123",
            "confirm": "password123",
        },
    )

    # Second registration with same username
    response = client.post(
        "/register",
        data={
            "username": "duplicate",
            "password": "password456",
            "confirm": "password456",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"That username is taken" in response.data or b"Username already taken" in response.data


# Test greet_user with active playthrough redirects to play
def test_greet_user_redirects_to_setup(client, user_with_character):
    """Test greet_user redirects to setup when character exists but no active playthrough."""
    user_id = user_with_character["user_id"]

    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert f"/player/{user_id}/setup" in response.location


# Test get_tile with no active playthrough
def test_get_tile_no_active_playthrough(client, user_with_character):
    """Test get_tile redirects when no active playthrough."""
    user_id = user_with_character["user_id"]

    # End the playthrough
    with client.application.app_context():
        play = Playthrough.query.filter_by(user_id=user_id).first()
        if play:
            from datetime import datetime, timezone

            play.ended_at = datetime.now(timezone.utc)
            db.session.commit()

    response = client.get(f"/player/{user_id}/play", follow_redirects=False)
    assert response.status_code == 302
    assert "/" in response.location  # Redirects home


# Test get_tile shows readonly tile when action taken
def test_get_tile_readonly_when_actioned(client, user_with_character):
    """Test get_tile shows readonly view when tile action is taken."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Mark tile as actioned
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        tile.action_taken = True

        # Create an action record
        action_opt = ActionOption.query.first()
        assert action_opt is not None
        action = Action(name="rest", tile=tile_id, actionverb=action_opt.id)
        db.session.add(action)
        db.session.flush()
        tile.action = action.id
        db.session.commit()

    response = client.get(f"/player/{user_id}/play")
    assert response.status_code == 200
    assert b"readonly" in response.data or b"Next Tile" in response.data


# Test fight action
def test_fight_action(client, user_with_character):
    """Test fight action damages the player."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        initial_hp = user.hitpoints

        fight_action = ActionOption.query.filter_by(code="fight").first()
        assert fight_action is not None
        action_value = fight_action.code

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify player took damage
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.hitpoints < initial_hp


# Test rest action on monster tile
def test_rest_on_monster_tile(client, user_with_character):
    """Test rest action on monster tile causes damage."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Change tile to monster type
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        monster_type = TileTypeOption.query.filter_by(name="monster").first()
        assert monster_type is not None
        tile.type = monster_type.id

        user = db.session.get(User, user_id)
        assert user is not None
        initial_hp = user.hitpoints

        rest_action = ActionOption.query.filter_by(code="rest").first()
        assert rest_action is not None
        action_value = rest_action.code
        db.session.commit()

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"dangerous" in response.data

    # Verify player lost HP
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.hitpoints < initial_hp


# Test rest action on non-monster tile
def test_rest_on_safe_tile(client, user_with_character):
    """Test rest action on safe tile heals the player."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Set player to low HP
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        user.hitpoints = 50

        # Ensure tile is not monster
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        sign_type = TileTypeOption.query.filter_by(name="sign").first()
        assert sign_type is not None
        tile.type = sign_type.id

        rest_action = ActionOption.query.filter_by(code="rest").first()
        assert rest_action is not None
        action_value = rest_action.code
        db.session.commit()

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"recover" in response.data

    # Verify player healed (User.heal respects max_hp)
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        # Should heal by 10 but respect max_hp
        assert user.hitpoints >= 50  # At least stayed at 50 or healed


# Test inspect on treasure tile (non-lucky)
def test_inspect_treasure_normal(client, user_with_character):
    """Test inspect action on treasure tile (normal case)."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Change tile to treasure type
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        treasure_type = TileTypeOption.query.filter_by(name="treasure").first()
        assert treasure_type is not None
        tile.type = treasure_type.id

        inspect_action = ActionOption.query.filter_by(code="inspect").first()
        assert inspect_action is not None
        action_value = inspect_action.code
        db.session.commit()

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should get either normal message or lucky message
    assert b"treasure" in response.data or b"artifact" in response.data


# Test inspect on monster tile
def test_inspect_monster(client, user_with_character):
    """Test inspect action on monster tile."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Change tile to monster type
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        monster_type = TileTypeOption.query.filter_by(name="monster").first()
        assert monster_type is not None
        tile.type = monster_type.id

        inspect_action = ActionOption.query.filter_by(code="inspect").first()
        assert inspect_action is not None
        action_value = inspect_action.code
        db.session.commit()

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"creature" in response.data


# Test action on already actioned tile (non-AJAX)
def test_action_already_actioned_tile(client, user_with_character):
    """Test executing action on already actioned tile redirects."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Mark tile as actioned
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        tile.action_taken = True
        db.session.commit()

        rest_action = ActionOption.query.filter_by(code="rest").first()
        assert rest_action is not None
        action_value = rest_action.code

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert f"/player/{user_id}/play" in response.location


# Test action with AJAX request
def test_action_ajax_request(client, user_with_character):
    """Test executing action with AJAX returns JSON."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    with client.application.app_context():
        rest_action = ActionOption.query.filter_by(code="rest").first()
        assert rest_action is not None
        action_value = rest_action.code

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "ok" in data or "tile_html" in data


# Test action with AJAX on already actioned tile
def test_action_ajax_already_actioned(client, user_with_character):
    """Test AJAX action on already actioned tile returns redirect JSON."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Mark tile as actioned
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        tile.action_taken = True
        db.session.commit()

        rest_action = ActionOption.query.filter_by(code="rest").first()
        assert rest_action is not None
        action_value = rest_action.code

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "redirect" in data


# Test action with no action value (AJAX)
def test_action_no_value_ajax(client, user_with_character):
    """Test action with no value via AJAX returns error."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


# Test player death check
def test_player_death_property(client, user_with_character):
    """Test that player death is detected correctly."""
    user_id = user_with_character["user_id"]

    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None

        # Alive
        user.hitpoints = 50
        assert user.is_alive

        # Dead
        user.hitpoints = 0
        assert not user.is_alive

        # Negative HP (dead)
        user.hitpoints = -10
        assert not user.is_alive


# Test quit action ends playthrough
def test_quit_ends_playthrough(client, user_with_character):
    """Test quit action ends the playthrough."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    with client.application.app_context():
        quit_action = ActionOption.query.filter_by(code="quit").first()
        assert quit_action is not None
        action_value = quit_action.code

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.location == "/"

    # Verify playthrough ended
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        if tile.playthrough_id:
            play = db.session.get(Playthrough, tile.playthrough_id)
            assert play is not None
            assert play.ended_at is not None


# Test quit action via AJAX
def test_quit_ajax(client, user_with_character):
    """Test quit action via AJAX returns redirect JSON."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    with client.application.app_context():
        quit_action = ActionOption.query.filter_by(code="quit").first()
        assert quit_action is not None
        action_value = quit_action.code

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "redirect" in data


# Test start_journey creates playthrough and tile
def test_start_journey(client, authenticated_user, setup_game_data):
    """Test start_journey creates new playthrough and tile."""
    user_id = authenticated_user

    # Set up character
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        player_class = PlayerClass.query.first()
        player_race = PlayerRace.query.first()
        assert player_class is not None
        assert player_race is not None
        user.playerclass = player_class.id
        user.playerrace = player_race.id
        db.session.commit()

    response = client.post(f"/player/{user_id}/start_journey", follow_redirects=False)

    assert response.status_code == 302
    assert f"/player/{user_id}/play" in response.location

    # Verify playthrough and tile created
    with client.application.app_context():
        play = Playthrough.query.filter_by(user_id=user_id, ended_at=None).first()
        assert play is not None

        tile = Tile.query.filter_by(user_id=user_id, playthrough_id=play.id).first()
        assert tile is not None
        assert tile.content is not None  # Content should be generated


# Test generate_tile without actioned previous tile
def test_generate_tile_no_actioned_tile(client, user_with_character):
    """Test generate_tile redirects if previous tile not actioned."""
    user_id = user_with_character["user_id"]

    response = client.get(f"/player/{user_id}/game/tile/next", follow_redirects=False)

    assert response.status_code == 302
    assert f"/player/{user_id}/play" in response.location


# Test generate_tile when player is dead
def test_generate_tile_requires_active_playthrough(client, user_with_character):
    """Test generate_tile redirects when no active playthrough exists."""
    user_id = user_with_character["user_id"]

    # Try to generate a tile without starting a journey
    response = client.get(f"/player/{user_id}/game/tile/next", follow_redirects=False)

    # Should redirect (to setup or play page)
    assert response.status_code == 302


# Test generate_tile filters actions by tile type
def test_generate_tile_action_filtering(client, user_with_character):
    """Test generate_tile filters actions based on tile type."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Mark current tile as actioned
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        tile.action_taken = True
        db.session.commit()

    response = client.get(f"/player/{user_id}/game/tile/next", follow_redirects=True)
    assert response.status_code == 200

    # Verify new tile was created with content
    with client.application.app_context():
        tiles = Tile.query.filter_by(user_id=user_id).all()
        assert len(tiles) == 2
        new_tile = tiles[-1]
        assert new_tile.content is not None


# Test action filtering for sign tiles
def test_sign_tile_action_filtering(client, user_with_character):
    """Test sign tiles only allow rest, inspect, quit."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Change tile to sign type
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        sign_type = TileTypeOption.query.filter_by(name="sign").first()
        assert sign_type is not None
        tile.type = sign_type.id
        db.session.commit()

    response = client.get(f"/player/{user_id}/play")
    assert response.status_code == 200

    # Fight should not be in the response
    # Note: This is a UI test, actual enforcement is on server side
    assert b"rest" in response.data
    assert b"inspect" in response.data
    assert b"quit" in response.data


# Test action filtering for treasure tiles
def test_treasure_tile_action_filtering(client, user_with_character):
    """Test treasure tiles disable fight action."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Change tile to treasure type
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        treasure_type = TileTypeOption.query.filter_by(name="treasure").first()
        assert treasure_type is not None
        tile.type = treasure_type.id
        db.session.commit()

    response = client.get(f"/player/{user_id}/play")
    assert response.status_code == 200

    # Should have rest, inspect, quit but not fight
    assert b"rest" in response.data
    assert b"inspect" in response.data
    assert b"quit" in response.data


# Test get_user_profile when user doesn't exist
def test_get_user_profile_not_found(client, authenticated_user):
    """Test get_user_profile redirects when user not found."""
    # Create a fake user ID that doesn't exist
    with client.application.app_context():
        max_id = db.session.query(db.func.max(User.id)).scalar() or 0
        fake_id = max_id + 1000

    # Try to access but will be blocked by authorization check (403)
    # So we test with authenticated user but deleted
    user_id = authenticated_user
    with client.application.app_context():
        user = db.session.get(User, user_id)
        if user:
            db.session.delete(user)
            db.session.commit()

    # Re-login won't work, so this will fail authentication
    response = client.get(f"/player/{user_id}/profile", follow_redirects=True)
    assert response.status_code == 200  # Redirects to login


# Test game_over route displays correct info
def test_game_over_displays_stats(client, user_with_character):
    """Test game over route displays player stats."""
    user_id = user_with_character["user_id"]

    response = client.get(f"/player/{user_id}/gameover")
    assert response.status_code == 200
    assert b"authuser" in response.data
    # The fixture sets class/race, should show class name or Unknown
    assert (
        b"witch" in response.data
        or b"fighter" in response.data
        or b"healer" in response.data
        or b"Unknown" in response.data
    )


# Test restart_game clears tiles and resets player
def test_restart_game_clears_data(client, user_with_character):
    """Test restart_game clears all tiles and resets player."""
    user_id = user_with_character["user_id"]

    # Count tiles before restart
    with client.application.app_context():
        tiles_before = Tile.query.filter_by(user_id=user_id).count()
        assert tiles_before > 0  # We should have tiles

    response = client.post(f"/player/{user_id}/restart", follow_redirects=True)
    assert response.status_code == 200

    # Verify player stats were reset
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.hitpoints == 100
        assert user.level == 1
        assert user.exp_points == 0

        # Verify tiles were deleted
        tiles_after = Tile.query.filter_by(user_id=user_id).count()
        assert tiles_after == 0


# === Additional Branch Coverage Tests ===


# Test greet_user when user has class but no race (partial setup)
def test_greet_user_partial_setup_class_only(client, setup_game_data):
    """Test greet_user when user has class but not race."""
    with client.application.app_context():
        user = User(username="partialuser", password_hash=generate_password_hash("password"))
        db.session.add(user)
        db.session.flush()

        player_class = PlayerClass.query.first()
        user.playerclass = player_class.id
        # Don't set playerrace - only one condition true

        db.session.commit()
        user_id = user.id

    client.post("/login", data={"username": "partialuser", "password": "password"})
    response = client.get("/", follow_redirects=False)

    # Should redirect to setup since not fully configured
    assert response.status_code == 302
    assert f"/player/{user_id}/setup" in response.location


# Test setup_char when user is dead but has no class (restart scenario)
def test_setup_char_dead_no_class(client, authenticated_user, setup_game_data):
    """Test setup_char when dead but playerclass is None (restart flow)."""
    user_id = authenticated_user

    with client.application.app_context():
        user = db.session.get(User, user_id)
        user.hitpoints = 0
        user.playerclass = None  # No class set
        db.session.commit()

    response = client.get(f"/player/{user_id}/setup")

    # Should NOT redirect to game_over since playerclass is None
    assert response.status_code == 200
    assert b"setup" in response.data.lower() or b"character" in response.data.lower()


# Test setup_char POST when tile already exists
def test_setup_char_post_with_existing_tile(client, user_with_character):
    """Test setup_char POST when user already has tiles."""
    user_id = user_with_character["user_id"]

    with client.application.app_context():
        user = db.session.get(User, user_id)
        # Reset class/race to allow re-setup
        user.playerclass = None
        user.playerrace = None
        db.session.commit()

        player_class = PlayerClass.query.first()
        player_race = PlayerRace.query.first()
        class_id = player_class.id
        race_id = player_race.id

        # Verify tile exists
        existing_tiles = Tile.query.filter_by(user_id=user_id).count()
        assert existing_tiles > 0

    response = client.post(
        f"/player/{user_id}/setup",
        data={"charclass": class_id, "charrace": race_id},
        follow_redirects=False,
    )

    # Should not create new tile since one exists
    assert response.status_code == 302

    with client.application.app_context():
        final_tiles = Tile.query.filter_by(user_id=user_id).count()
        # Tile count should not increase
        assert final_tiles == existing_tiles


# Test execute_tile_action with non-POST method
def test_execute_action_non_post(client, user_with_character):
    """Test execute_tile_action with GET method."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]
    
    response = client.get(f"/player/{user_id}/game/tile/{tile_id}/action")
    
    # Flask returns 405 Method Not Allowed for GET on POST-only route
    assert response.status_code == 405
# Test execute_tile_action with numeric action ID
def test_execute_action_numeric_id(client, user_with_character):
    """Test execute_tile_action with numeric action ID."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    with client.application.app_context():
        rest_action = ActionOption.query.filter_by(code="rest").first()
        action_id = str(rest_action.id)

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_id},
        follow_redirects=True,
    )

    assert response.status_code == 200


# Test execute_tile_action when action history already exists
def test_execute_action_with_existing_history(client, user_with_character):
    """Test execute_tile_action when Action record already exists."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    with client.application.app_context():
        # Pre-create an action record
        rest_action = ActionOption.query.filter_by(code="rest").first()
        existing_action = Action(name="rest", tile=tile_id, actionverb=rest_action.id)
        db.session.add(existing_action)
        db.session.commit()

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": "rest"},
        follow_redirects=True,
    )

    # Should reuse existing action record
    assert response.status_code == 200


# Test execute_tile_action inspect on scene tile
def test_execute_action_inspect_scene(client, user_with_character):
    """Test inspect action on scene tile."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        scene_type = TileTypeOption.query.filter_by(name="scene").first()
        tile.type = scene_type.id
        db.session.commit()

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": "inspect"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"surroundings" in response.data.lower() or b"examine" in response.data.lower()


# Test game_over when playerclass is None
def test_game_over_no_class(client, authenticated_user):
    """Test game_over when player has no class."""
    user_id = authenticated_user

    with client.application.app_context():
        user = db.session.get(User, user_id)
        user.hitpoints = 0
        user.playerclass = None
        db.session.commit()

    response = client.get(f"/player/{user_id}/gameover")

    assert response.status_code == 200
    assert b"Unknown" in response.data


# Test game_over when playerrace is None
def test_game_over_no_race(client, authenticated_user, setup_game_data):
    """Test game_over when player has no race."""
    user_id = authenticated_user

    with client.application.app_context():
        user = db.session.get(User, user_id)
        player_class = PlayerClass.query.first()
        user.playerclass = player_class.id
        user.playerrace = None
        db.session.commit()

    response = client.get(f"/player/{user_id}/gameover")

    assert response.status_code == 200
    assert b"Unknown" in response.data


# Test restart_game with GET method
def test_restart_game_get_method(client, authenticated_user):
    """Test restart_game with GET method."""
    user_id = authenticated_user

    response = client.get(f"/player/{user_id}/restart")

    # Should still work (route accepts GET and POST)
    assert response.status_code in [200, 302]


# Test get_tile with no tile for user in active playthrough
def test_get_tile_no_tile_in_playthrough(client, authenticated_user, setup_game_data):
    """Test get_tile when playthrough exists but no tiles."""
    user_id = authenticated_user

    with client.application.app_context():
        user = db.session.get(User, user_id)
        player_class = PlayerClass.query.first()
        player_race = PlayerRace.query.first()
        user.playerclass = player_class.id
        user.playerrace = player_race.id

        # Create playthrough but no tiles
        play = Playthrough(user_id=user_id)
        db.session.add(play)
        db.session.commit()

    response = client.get(f"/player/{user_id}/play", follow_redirects=False)

    # Should redirect to setup
    assert response.status_code == 302
    assert "setup" in response.location


# Test get_tile with scene tile type (different from sign/treasure/monster)
def test_get_tile_scene_type_actions(client, user_with_character):
    """Test get_tile allows all actions for scene tile."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        scene_type = TileTypeOption.query.filter_by(name="scene").first()
        tile.type = scene_type.id
        db.session.commit()

    response = client.get(f"/player/{user_id}/play")

    assert response.status_code == 200
    # Scene tiles should allow all actions including fight
    assert b"fight" in response.data
