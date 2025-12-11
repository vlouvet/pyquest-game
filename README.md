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

- ✅ Fixed security vulnerabilities (authorization checks, secret key management)
- ✅ Removed code duplication between `__init__.py` and `app.py`
- ✅ Converted to proper Blueprint architecture
- ✅ Added comprehensive configuration management
- ✅ Improved database models with relationships and helper methods
- ✅ Added CSS styling for better UX
- ✅ Enhanced User model with game stats (strength, intelligence, stealth, etc.)
- ✅ Fixed form validation issues

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

```bash
pytest
# Or with coverage
pytest --cov=pq_app tests/
```

## Project Structure

```
pyquest-game/
├── pq_app/
│   ├── __init__.py          # Application factory
│   ├── app.py               # Main blueprint with routes
│   ├── model.py             # Database models
│   ├── gameforms.py         # WTForms definitions
│   ├── pqMonsters.py        # Monster generation
│   ├── gameTile.py          # Tile generation logic
│   ├── static/
│   │   └── styles.css       # CSS styling
│   └── templates/           # Jinja2 templates
├── tests/                   # Test suite
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

## Game Flow

1. **Register/Login**: Create an account or log in
2. **Character Setup**: Choose your race (Human, Elf, Pandarian) and class (Witch, Fighter, Healer)
3. **Explore Tiles**: Navigate through randomly generated tiles
4. **Take Actions**: Rest, inspect, fight, or quit on each tile
5. **Progress**: Build your character through experience and items

## Database Schema

- **User**: Player accounts with stats (HP, strength, intelligence, stealth, level, etc.)
- **Tile**: Individual game tiles with types and actions
- **Action**: Actions performed on tiles
- **ActionOption**: Available action types
- **TileTypeOption**: Tile categories (monster, sign, scene, treasure)
- **PlayerClass**: Character classes
- **PlayerRace**: Character races

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## TODO / Roadmap

- [ ] Implement combat system for monster tiles
- [ ] Add treasure/inventory system
- [ ] Implement character stat bonuses from race/class
- [ ] Add pagination to game history
- [ ] Create API endpoints for mobile app
- [ ] Add achievement system
- [ ] Implement leaderboards
- [ ] Add database migrations with Flask-Migrate
- [ ] Improve test coverage (target: 80%+)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- Original Author: vlouvet
- Contributors: See GitHub contributors list

## Acknowledgments

- Flask and Flask-SQLAlchemy communities
- Python roguelike game developers

