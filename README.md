# PyQuest Game

A text-based RPG game with roguelike elements, written in Python using Flask.

## Features

- 🎮 **Web-based Interface**: Play through your browser with Flask
- 🗄️ **Persistent Storage**: Uses Flask-SQLAlchemy with SQLite3 to store player data
- 🎲 **Procedural Generation**: Random tile categories for unique gameplay
- 👤 **User Authentication**: Secure registration and login system
- ⚔️ **Character System**: Choose your race and class
- 🎯 **Tile-based Progression**: Navigate through different tile types (monsters, signs, scenes, treasures)
- 📊 **Game History**: Track your adventure progress

## Recent Improvements (Dec 2025)

### Architecture & Code Quality
- ✅ Fixed security vulnerabilities (authorization checks, secret key management)
- ✅ Removed code duplication between `__init__.py` and `app.py`
- ✅ Converted to proper Blueprint architecture
- ✅ Added comprehensive configuration management
- ✅ Improved database models with relationships and helper methods
- ✅ Added CSS styling for better UX
- ✅ Enhanced User model with game stats (strength, intelligence, stealth, etc.)
- ✅ Fixed form validation issues
- ✅ Implemented service layer pattern (CombatService, TileService, MediaService)

### Combat System
- ✅ **Fully implemented combat system** with CombatAction model
- ✅ Combat actions with damage, healing, defense mechanics
- ✅ Class and race-specific combat abilities
- ✅ Encounter tracking system with combat history
- ✅ Combat API endpoints with JWT authentication

### Database & Migrations
- ✅ **Database migrations with Alembic** (6 migrations implemented)
- ✅ Playthrough tracking system
- ✅ ASCII art support for tiles
- ✅ Combat encounter and media tables

### API & Testing
- ✅ **RESTful API with OpenAPI/Swagger documentation** (`/api/docs`)
- ✅ JWT authentication for API endpoints
- ✅ Comprehensive test suite: **95/96 tests passing** (99% pass rate)
- ✅ **77% code coverage** across the application
- ✅ Fixed user_id/player_id consistency issues

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/vlouvet/pyquest-game.git
   cd pyquest-game
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your SECRET_KEY
   ```

5. **Generate a secret key** (recommended for production)
   ```bash
   python -c 'import secrets; print(secrets.token_hex(32))'
   # Copy the output to your .env file as SECRET_KEY
   ```

## Running the Application

### Development Mode

```bash
python run.py
```

Then open your browser to `http://localhost:5000`

### Production Mode

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "pq_app:create_app()"
```

## Testing

The project has a comprehensive test suite with **95/96 tests passing** (99% pass rate) and **77% code coverage**.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=pq_app tests/

# Run with detailed coverage
pytest --cov=pq_app --cov-report=html tests/
# Then open htmlcov/index.html in your browser

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::TestAuth::test_register
```

Test coverage by module:
- API endpoints: 75-100%
- Models: 96%
- Services: 53-83%
- Overall: 77%

## Project Structure

```
pyquest-game/
├── pq_app/
│   ├── __init__.py          # Application factory
│   ├── app.py               # Main blueprint with routes
│   ├── model.py             # Database models (User, Tile, Combat, etc.)
│   ├── gameforms.py         # WTForms definitions
│   ├── pqMonsters.py        # Monster generation
│   ├── gameTile.py          # Tile generation logic
│   ├── api/                 # RESTful API endpoints
│   │   ├── auth.py          # JWT authentication
│   │   ├── combat.py        # Combat API
│   │   ├── player.py        # Player/character API
│   │   ├── tiles.py         # Tile navigation API
│   │   ├── schemas.py       # Marshmallow schemas
│   │   ├── docs.py          # Swagger/OpenAPI docs
│   │   └── openapi.yaml     # API specification
│   ├── services/            # Business logic layer
│   │   ├── combat_service.py   # Combat mechanics
│   │   ├── tile_service.py     # Tile generation/management
│   │   └── media_service.py    # ASCII art/media handling
│   ├── static/
│   │   └── styles.css       # CSS styling
│   └── templates/           # Jinja2 templates
├── alembic/                 # Database migrations
│   └── versions/            # Migration scripts
├── tests/                   # Comprehensive test suite (95+ tests)
├── config.py                # Configuration classes
├── run.py                   # Development server script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration

The app uses three configuration profiles:

- **Development**: Debug mode enabled, local SQLite database
- **Testing**: In-memory database, CSRF disabled
- **Production**: Secure settings, must set SECRET_KEY via environment

Set the environment via `FLASK_ENV` variable:
```bash
export FLASK_ENV=production
```

## Database Migrations

The project uses Alembic for database migrations:

```bash
# Initialize the database (first time only)
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

Current migrations:
1. ✅ Add ActionOption code field
2. ✅ Add ON DELETE CASCADE for actions
3. ✅ Make ActionOption code not nullable
4. ✅ Add Playthrough model
5. ✅ Add ASCII art to TileTypeOption
6. ✅ Add Combat, Encounter, and Media tables

## Game Flow

### Web Interface
1. **Register/Login**: Create an account or log in
2. **Character Setup**: Choose your race (Human, Elf, Pandarian) and class (Witch, Fighter, Healer)
3. **Start Journey**: Begin a new playthrough
4. **Explore Tiles**: Navigate through randomly generated tiles
5. **Combat**: Fight monsters using various combat actions (attack, defend, heal, flee)
6. **Take Actions**: Rest, inspect, or explore on each tile
7. **Progress**: Build your character through experience and track your combat history
8. **Game Over**: Review stats and restart or view history

### API Interface
Use the RESTful API to build custom clients:
- Authenticate with JWT tokens
- Get current tile and available actions
- Execute combat actions and tile interactions
- Retrieve player stats and encounter history
- Full OpenAPI/Swagger documentation available

## Database Schema

### Core Models
- **User**: Player accounts with stats (HP, strength, intelligence, stealth, level, XP, etc.)
- **Tile**: Individual game tiles with types, actions, and content
- **Playthrough**: Game sessions tracking player progress
- **Action**: Actions performed on tiles
- **ActionOption**: Available action types with unique codes
- **TileTypeOption**: Tile categories (monster, sign, scene, treasure) with ASCII art

### Character System
- **PlayerClass**: Character classes (Witch, Fighter, Healer)
- **PlayerRace**: Character races (Human, Elf, Pandarian)

### Combat System
- **CombatAction**: Combat moves with damage, healing, and defense stats
- **Encounter**: Combat history tracking damage dealt/received and outcomes

### Media System
- **TileMedia**: ASCII art and visual content for tiles
- **CombatEncounterMedia**: Media assets for combat encounters

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## API Documentation

The game includes a full RESTful API with JWT authentication:

- **Swagger UI**: Access interactive API docs at `/api/docs` when running the app
- **Authentication**: Register/login to get JWT tokens
- **Endpoints**:
  - `/api/v1/auth/*` - User registration and authentication
  - `/api/v1/player/*` - Character management and stats
  - `/api/v1/player/{id}/tiles/*` - Tile navigation and actions
  - `/api/v1/player/{id}/combat/*` - Combat execution and history
  - `/api/v1/player/{id}/encounters` - Combat encounter history

Example API usage:
```bash
# Login and get token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "password"}'

# Get current tile (use token from login)
curl http://localhost:5000/api/v1/player/1/tiles/current \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## TODO / Roadmap

### Completed ✅
- ✅ Implement combat system for monster tiles
- ✅ Create API endpoints for mobile app
- ✅ Add database migrations with Alembic
- ✅ Improve test coverage (achieved: 77%, target: 80%)

### In Progress / Planned 🔄
- [ ] Add treasure/inventory system
- [ ] Implement character stat bonuses from race/class
- [ ] Add pagination to game history
- [ ] Add achievement system
- [ ] Implement leaderboards
- [ ] Reach 80%+ test coverage (currently 77%)
- [ ] Add WebSocket support for real-time multiplayer
- [ ] Implement procedural dungeon generation
- [ ] Add item crafting system

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- Original Author: vlouvet
- Contributors: See GitHub contributors list

## Acknowledgments

- Flask and Flask-SQLAlchemy communities
- Python roguelike game developers

