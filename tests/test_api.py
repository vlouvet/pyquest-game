"""
API Tests

Tests for REST API endpoints including authentication, players, tiles, and combat.
"""
import pytest
import json
from pq_app import create_app
from pq_app.model import db, User, User, Tile, TileTypeOption, ActionOption, CombatAction, Playthrough
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create test app"""
    app = create_app('testing')
    
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
def auth_headers(client):
    """Create user and return auth headers"""
    # Register user
    client.post('/api/v1/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123!'
    })
    
    # Login
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'TestPass123!'
    })
    
    data = json.loads(response.data)
    access_token = data['access_token']
    
    return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture
def test_character(app, auth_headers, client):
    """Get the test user's character (User IS the character in this implementation)"""
    # Get the list of characters (which is just the authenticated user)
    response = client.get('/api/v1/player/characters', 
                         headers=auth_headers)
    
    data = json.loads(response.data)
    # Return the first (and only) character from the list
    return data['characters'][0]


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'User created successfully'
        assert data['user']['username'] == 'newuser'
        assert 'pw_hash' not in data['user']
    
    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username"""
        # First registration
        client.post('/api/v1/auth/register', json={
            'username': 'duplicate',
            'email': 'first@example.com',
            'password': 'Pass123!'
        })
        
        # Duplicate registration
        response = client.post('/api/v1/auth/register', json={
            'username': 'duplicate',
            'email': 'second@example.com',
            'password': 'Pass123!'
        })
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'already exists' in data['message'].lower()
    
    def test_register_missing_fields(self, client):
        """Test registration with missing fields"""
        response = client.post('/api/v1/auth/register', json={
            'username': 'incomplete'
        })
        
        assert response.status_code == 400
    
    def test_login_success(self, client):
        """Test successful login"""
        # Register first
        client.post('/api/v1/auth/register', json={
            'username': 'logintest',
            'email': 'login@example.com',
            'password': 'LoginPass123!'
        })
        
        # Login
        response = client.post('/api/v1/auth/login', json={
            'username': 'logintest',
            'password': 'LoginPass123!'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['username'] == 'logintest'
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/v1/auth/login', json={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info"""
        response = client.get('/api/v1/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['username'] == 'testuser'
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get('/api/v1/auth/me')
        
        assert response.status_code == 401


class TestUsers:
    """Test player character endpoints"""
    
    def test_create_character(self, client, auth_headers):
        """Test that character creation returns 409 (User IS the character)"""
        response = client.post('/api/v1/player/characters',
                              headers=auth_headers,
                              json={
                                  'char_name': 'Aragorn',
                                  'char_class': 'ranger',
                                  'char_race': 'human'
                              })
        
        # In this implementation, users already have a character
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['error'] == 'Conflict'
        assert 'already has a character' in data['message']
    
    def test_create_character_missing_fields(self, client, auth_headers):
        """Test that character creation returns 409 regardless of fields"""
        response = client.post('/api/v1/player/characters',
                              headers=auth_headers,
                              json={'char_name': 'Incomplete'})
        
        # Still returns 409 because users already have a character
        assert response.status_code == 409
    
    def test_get_all_characters(self, client, auth_headers, test_character):
        """Test getting all user characters"""
        response = client.get('/api/v1/player/characters', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['characters']) >= 1
        # Character name is the username
        assert data['characters'][0]['char_name'] == test_character['char_name']
    
    def test_get_character_by_id(self, client, auth_headers, test_character):
        """Test getting specific character"""
        char_id = test_character['id']
        response = client.get(f'/api/v1/player/characters/{char_id}',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == char_id
        # Character name is the username
        assert data['char_name'] == test_character['char_name']
    
    def test_get_character_not_found(self, client, auth_headers):
        """Test getting non-existent character"""
        response = client.get('/api/v1/player/characters/99999',
                            headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_update_character(self, client, auth_headers, test_character):
        """Test updating character"""
        char_id = test_character['id']
        response = client.patch(f'/api/v1/player/characters/{char_id}',
                               headers=auth_headers,
                               json={
                                   'hit_points': 75,
                                   'experience': 500
                               })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['character']['hit_points'] == 75
        assert data['character']['experience'] == 500
    
    def test_get_character_stats(self, client, auth_headers, test_character):
        """Test getting character statistics"""
        char_id = test_character['id']
        response = client.get(f'/api/v1/player/characters/{char_id}/stats',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'character' in data
        assert 'statistics' in data
        assert 'total_encounters' in data['statistics']


class TestTiles:
    """Test tile endpoints"""
    
    def test_get_current_tile(self, app, client, auth_headers, test_character):
        """Test getting current tile"""
        # Create playthrough and tile
        with app.app_context():
            player = db.session.get(User, test_character['id'])
            
            # Create playthrough
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()
            
            # Create tile
            tile = Tile(type=1, content="Test tile", playthrough_id=playthrough.id, user_id=player.id)
            db.session.add(tile)
            db.session.commit()
        
        player_id = test_character['id']
        response = client.get(f'/api/v1/player/{player_id}/tiles/current',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'id' in data
        assert 'content' in data
        assert 'ascii_art' in data or data['ascii_art'] is None
    
    def test_get_tile_by_id(self, app, client, auth_headers, test_character):
        """Test getting specific tile"""
        # Create tile
        with app.app_context():
            player = db.session.get(User, test_character['id'])
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()
            
            tile = Tile(type=2, content="Specific tile", playthrough_id=playthrough.id, user_id=player.id)
            db.session.add(tile)
            db.session.commit()
            tile_id = tile.id
        
        player_id = test_character['id']
        response = client.get(f'/api/v1/player/{player_id}/tiles/{tile_id}',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == tile_id
        assert data['content'] == "Specific tile"


class TestCombat:
    """Test combat endpoints"""
    
    def test_get_combat_actions(self, app, client, auth_headers, test_character):
        """Test getting available combat actions"""
        # Create tile
        with app.app_context():
            player = db.session.get(User, test_character['id'])
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()
            
            tile = Tile(type=1, content="Monster tile", playthrough_id=playthrough.id)
            db.session.add(tile)
            db.session.commit()
            tile_id = tile.id
        
        player_id = test_character['id']
        response = client.get(
            f'/api/v1/player/{player_id}/tiles/{tile_id}/combat-actions',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'available_actions' in data
        assert len(data['available_actions']) > 0
    
    def test_execute_combat_action(self, app, client, auth_headers, test_character):
        """Test executing a combat action"""
        # Create tile and ensure combat action exists
        with app.app_context():
            player = db.session.get(User, test_character['id'])
            playthrough = Playthrough(user_id=player.id)
            db.session.add(playthrough)
            db.session.flush()
            
            tile = Tile(type=1, content="Combat tile", playthrough_id=playthrough.id, user_id=player.id)
            db.session.add(tile)
            db.session.commit()
            tile_id = tile.id
            
            # Check if combat action exists
            action = CombatAction.query.filter_by(code='attack_light').first()
            assert action is not None
        
        player_id = test_character['id']
        response = client.post(
            f'/api/v1/player/{player_id}/combat/execute',
            headers=auth_headers,
            json={
                'tile_id': tile_id,
                'combat_action_code': 'attack_light'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data
        assert 'message' in data
        assert 'player_hp' in data
    
    def test_get_encounters(self, client, auth_headers, test_character):
        """Test getting encounter history"""
        player_id = test_character['id']
        response = client.get(
            f'/api/v1/player/{player_id}/encounters',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'encounters' in data
        assert 'total' in data
        assert isinstance(data['encounters'], list)


class TestAPIDocs:
    """Test API documentation endpoints"""
    
    def test_api_root(self, client):
        """Test API root endpoint"""
        response = client.get('/api/v1/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'PyQuest API'
        assert 'version' in data
        assert 'documentation' in data
    
    def test_openapi_spec(self, client):
        """Test OpenAPI spec is accessible"""
        response = client.get('/api/v1/openapi.yaml')
        
        assert response.status_code == 200
        assert b'openapi' in response.data
    
    def test_swagger_docs(self, client):
        """Test Swagger UI docs endpoint"""
        response = client.get('/api/v1/docs')
        
        assert response.status_code == 200
        assert b'swagger' in response.data.lower()
