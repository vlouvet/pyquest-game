# # tests/test_routes.py
# from pq_app import app
# from config import TestingConfig

# import pytest
import pytest
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


def test_home_redirect(client):
    """Test that the home route redirects to login for unauthenticated users."""
    response = client.get("/")
    assert response.status_code == 302  # HTTP status for redirect
    assert b"/login?next=%2F" in response.data


@pytest.fixture
def setup_test_user(client):
    """Fixture to add a test user to the database."""
    with client.application.app_context():
        user = User(username="testuser")
        user.set_password("testpassword")  # Use the set_password method
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
    assert b'<input type=submit value="Setup">' in response.data  # Replace with the expected greeting message


def test_login_post_failure(client):
    """Test a failed POST login."""
    response = client.post(
        "/login",
        data={"username": "invaliduser", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Login" in response.data


def test_register_get(client):
    """Test the GET request to the register route."""
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Register" in response.data


def test_register_post_success(client):
    """Test a successful POST registration."""
    response = client.post(
        "/register",
        data={
            "username": "newuser",
            "password": "password123",
            "confirm": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Login" in response.data

    # Verify user was created in database
    with client.application.app_context():
        user = User.query.filter_by(username="newuser").first()
        assert user is not None


def test_logout(client, setup_test_user):
    """Test the logout route."""
    # First login
    client.post(
        "/login",
        data={"username": "testuser", "password": "testpassword"},
        follow_redirects=True,
    )

    # Then logout
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data


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

        # Add ActionOption (create codes for UI to post)
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


def test_setup_char_get(client, authenticated_user, setup_game_data):
    """Test GET request to character setup."""
    response = client.get(f"/player/{authenticated_user}/setup")
    assert response.status_code == 200
    assert b"charsetup" in response.data or b"Setup" in response.data


def test_setup_char_post(client, authenticated_user, setup_game_data):
    """Test POST request to character setup."""
    with client.application.app_context():
        player_class = PlayerClass.query.first()
        player_race = PlayerRace.query.first()
        # Ensure fixtures exist for type checkers and runtime
        assert player_class is not None
        assert player_race is not None

    response = client.post(
        f"/player/{authenticated_user}/setup",
        data={
            "charclass": player_class.id,
            "charrace": player_race.id,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verify user was updated
    with client.application.app_context():
        user = db.session.get(User, authenticated_user)
        # Ensure user exists
        assert user is not None
        assert user.playerclass == player_class.id
        assert user.playerrace == player_race.id


def test_setup_char_unauthorized(client, authenticated_user, setup_game_data):
    """Test that users cannot access other users' setup pages."""
    # Try to access a different user's setup page
    response = client.get(f"/player/{authenticated_user + 999}/setup")
    assert response.status_code == 403


def test_char_start(client, authenticated_user, setup_game_data):
    """Test the character start route."""
    response = client.get(f"/player/{authenticated_user}/start")
    assert response.status_code == 200
    assert b"charStart" in response.data or b"test message" in response.data


def test_char_start_unauthorized(client, authenticated_user):
    """Test that users cannot access other users' start pages."""
    response = client.get(f"/player/{authenticated_user + 999}/start")
    assert response.status_code == 403


@pytest.fixture
def user_with_character(client, authenticated_user, setup_game_data):
    """Fixture to create a user with character setup complete and a tile."""
    with client.application.app_context():
        user = db.session.get(User, authenticated_user)
        player_class = PlayerClass.query.first()
        player_race = PlayerRace.query.first()
        tile_type = TileTypeOption.query.first()

        # Ensure query results exist for static analysis and runtime
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

        tile = Tile(user_id=user.id, type=tile_type.id, action_taken=False, playthrough_id=play.id)
        db.session.add(tile)
        db.session.commit()

        tile_id = tile.id

    return {"user_id": authenticated_user, "tile_id": tile_id}


def test_get_tile(client, user_with_character):
    """Test getting the current tile."""
    user_id = user_with_character["user_id"]
    response = client.get(f"/player/{user_id}/play")
    assert response.status_code == 200
    assert b"gameTile" in response.data or b"Tile" in response.data


def test_get_tile_unauthorized(client, user_with_character):
    """Test that users cannot access other users' tiles."""
    user_id = user_with_character["user_id"]
    response = client.get(f"/player/{user_id + 999}/play")
    assert response.status_code == 403


def test_tile_type_content_generation(client, user_with_character):
    """Test that tile content is generated based on tile type."""
    user_id = user_with_character["user_id"]

    # Test different tile types
    with client.application.app_context():
        tile = Tile.query.filter_by(user_id=user_id).first()
        assert tile is not None

        # Test scene tile
        scene_type = TileTypeOption.query.filter_by(name="scene").first()
        assert scene_type is not None
        tile.type = scene_type.id
        db.session.commit()

    response = client.get(f"/player/{user_id}/play")
    assert response.status_code == 200
    assert b"This is a scene tile" in response.data

    # Test monster tile
    with client.application.app_context():
        tile = Tile.query.filter_by(user_id=user_id).first()
        assert tile is not None
        monster_type = TileTypeOption.query.filter_by(name="monster").first()
        assert monster_type is not None
        tile.type = monster_type.id
        db.session.commit()

    response = client.get(f"/player/{user_id}/play")
    assert response.status_code == 200
    # Monster name should appear (generated from NPCMonster)
    assert (
        b"elephant" in response.data
        or b"giraffe" in response.data
        or b"gryffon" in response.data
        or b"dragon" in response.data
    )


def test_execute_tile_action(client, user_with_character):
    """Test executing an action on a tile."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    with client.application.app_context():
        action = ActionOption.query.first()
        assert action is not None
        action_value = action.code or str(action.id)

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verify tile was marked as actioned
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        assert tile.action_taken is True


def test_execute_tile_action_unauthorized(client, user_with_character):
    """Test that users cannot execute actions on other users' tiles."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    response = client.post(
        f"/player/{user_id + 999}/game/tile/{tile_id}/action",
        data={"action": 1},
    )
    assert response.status_code == 403


def test_generate_tile(client, user_with_character):
    """Test generating a new tile."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # First mark the current tile as actioned
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        tile.action_taken = True
        db.session.commit()

    response = client.get(f"/player/{user_id}/game/tile/next", follow_redirects=True)
    assert response.status_code == 200


def test_generate_tile_unauthorized(client, user_with_character):
    """Test that users cannot generate tiles for other users."""
    user_id = user_with_character["user_id"]
    response = client.get(f"/player/{user_id + 999}/game/tile/next")
    assert response.status_code == 403


def test_get_user_profile(client, authenticated_user):
    """Test getting user profile."""
    response = client.get(f"/player/{authenticated_user}/profile")
    assert response.status_code == 200
    assert b"profile" in response.data or b"authuser" in response.data


def test_get_user_profile_unauthorized(client, authenticated_user):
    """Test that users cannot access other users' profiles."""
    response = client.get(f"/player/{authenticated_user + 999}/profile")
    assert response.status_code == 403


def test_get_history(client, user_with_character):
    """Test getting game history."""
    user_id = user_with_character["user_id"]
    response = client.get(f"/player/{user_id}/game/history")
    assert response.status_code == 200
    assert b"history" in response.data or b"History" in response.data


def test_get_history_unauthorized(client, user_with_character):
    """Test that users cannot access other users' history."""
    user_id = user_with_character["user_id"]
    response = client.get(f"/player/{user_id + 999}/game/history")
    assert response.status_code == 403


def test_game_over_when_hp_zero(client, user_with_character):
    """Test that User.is_alive property and take_damage work correctly."""
    user_id = user_with_character["user_id"]

    # Test the is_alive property and take_damage method
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None

        # User should be alive initially
        assert user.is_alive
        assert user.hitpoints > 0

        # Take damage but stay alive
        initial_hp = user.hitpoints
        user.take_damage(10)
        assert user.hitpoints == initial_hp - 10
        assert user.is_alive

        # Take fatal damage
        user.take_damage(user.hitpoints + 10)
        assert user.hitpoints == 0
        assert not user.is_alive


def test_game_over_route(client, user_with_character):
    """Test the game over route displays correctly."""
    user_id = user_with_character["user_id"]

    # Set player to dead
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        user.hitpoints = 0
        db.session.commit()

    response = client.get(f"/player/{user_id}/gameover")
    assert response.status_code == 200
    assert b"Game Over" in response.data
    assert b"authuser" in response.data


def test_restart_game(client, user_with_character):
    """Test restarting the game redirects to setup."""
    user_id = user_with_character["user_id"]

    # Restart the game
    response = client.post(
        f"/player/{user_id}/restart",
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should redirect to character setup
    assert b"setup" in response.data or b"charsetup" in response.data.lower()


def test_heal_respects_max_hp(client, user_with_character):
    """Test that healing with rest action respects max HP."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Set player HP to max
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        user.hitpoints = user.max_hp
        db.session.commit()

    # Execute rest action by code
    with client.application.app_context():
        rest_action = ActionOption.query.filter_by(code="rest").first()
        assert rest_action is not None
        action_value = rest_action.code or str(rest_action.id)

    client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=True,
    )

    # Verify HP didn't exceed max
    with client.application.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        assert user.hitpoints == user.max_hp
        assert user.hitpoints <= 100


def test_inspect_action(client, user_with_character):
    """Test that inspect action works correctly."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Get inspect action code
    with client.application.app_context():
        inspect_action = ActionOption.query.filter_by(code="inspect").first()
        assert inspect_action is not None
        action_value = inspect_action.code or str(inspect_action.id)

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify tile was actioned and inspect was processed
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        assert tile.action_taken is True
        # tile.action stores the Action history id; verify the history references the ActionOption
        action_history = db.session.get(Action, tile.action)
        assert action_history is not None
        # Resolve the ActionOption id and compare
        inspect_action_db = ActionOption.query.filter_by(code="inspect").first()
        assert inspect_action_db is not None
        assert action_history.actionverb == inspect_action_db.id


def test_quit_action(client, user_with_character):
    """Test that quit action works correctly."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]

    # Get quit action code
    with client.application.app_context():
        quit_action = ActionOption.query.filter_by(code="quit").first()
        assert quit_action is not None
        action_value = quit_action.code or str(quit_action.id)

    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_value},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify tile was actioned and quit was processed
    with client.application.app_context():
        tile = db.session.get(Tile, tile_id)
        assert tile is not None
        assert tile.action_taken is True
        # tile.action stores the Action history id; verify the history references the ActionOption
        action_history = db.session.get(Action, tile.action)
        assert action_history is not None
        quit_action_db = ActionOption.query.filter_by(code="quit").first()
        assert quit_action_db is not None
        assert action_history.actionverb == quit_action_db.id
