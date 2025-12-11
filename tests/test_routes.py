# # tests/test_routes.py
# from pq_app import app
# from config import TestingConfig

# import pytest
import pytest
from werkzeug.security import generate_password_hash
from pq_app import create_app
from pq_app.model import User, db, PlayerClass, PlayerRace, Tile, TileTypeOption, ActionOption, Action


def test_home_redirect(client):
    """Test that the home route redirects to login for unauthenticated users."""
    response = client.get("/")
    assert response.status_code == 302  # HTTP status for redirect
    assert b"/login?next=%2F" in response.data


@pytest.fixture
def setup_test_user(client):
    """Fixture to add a test user to the database."""
    with client.application.app_context():
        user = User(
            username="testuser", password_hash=generate_password_hash("testpassword")
        )
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
    assert (
        b'<input type=submit value="Setup">' in response.data
    )  # Replace with the expected greeting message


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
        data={"username": "newuser", "password": "password123", "confirm": "password123"},
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
        user = User(
            username="authuser", password_hash=generate_password_hash("password123")
        )
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
            rest = ActionOption(name="Rest")
            explore = ActionOption(name="Explore")
            fight = ActionOption(name="Fight")
            db.session.add(rest)
            db.session.add(explore)
            db.session.add(fight)
        
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
        user = User.query.get(authenticated_user)
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
        user = User.query.get(authenticated_user)
        player_class = PlayerClass.query.first()
        player_race = PlayerRace.query.first()
        tile_type = TileTypeOption.query.first()
        
        user.playerclass = player_class.id
        user.playerrace = player_race.id
        user.hitpoints = 100
        
        # Create a tile for the user
        tile = Tile(user_id=user.id, type=tile_type.id, action_taken=False)
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


def test_execute_tile_action(client, user_with_character):
    """Test executing an action on a tile."""
    user_id = user_with_character["user_id"]
    tile_id = user_with_character["tile_id"]
    
    with client.application.app_context():
        action = ActionOption.query.first()
        action_id = action.id
    
    response = client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    
    # Verify tile was marked as actioned
    with client.application.app_context():
        tile = Tile.query.get(tile_id)
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
        tile = Tile.query.get(tile_id)
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
        user = User.query.get(user_id)
        
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
        user = User.query.get(user_id)
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
        user = User.query.get(user_id)
        user.hitpoints = user.max_hp
        db.session.commit()
    
    # Execute rest action (ID 1 based on init_defaults)
    action_id = 1
    
    client.post(
        f"/player/{user_id}/game/tile/{tile_id}/action",
        data={"action": action_id},
        follow_redirects=True,
    )
    
    # Verify HP didn't exceed max
    with client.application.app_context():
        user = User.query.get(user_id)
        assert user.hitpoints == user.max_hp
        assert user.hitpoints <= 100

