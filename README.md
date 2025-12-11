# PyQuest Game

A text-based RPG with roguelike elements, built with Flask.

## Features

- 🎮 Web UI with Flask
- 🗄️ SQLite by default (SQLAlchemy); Alembic migrations
- 🎲 Procedural tiles and combat encounters
- 👤 Auth + player stats (class/race, HP, attributes)
- 🔐 REST API with JWT and Swagger docs

## Quick Start

```bash
git clone https://github.com/vlouvet/pyquest-game.git
cd pyquest-game
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```
Then open http://localhost:5000

Set a secret key (recommended):
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```
Add the value to your `.env` as `SECRET_KEY` (create the file if missing).

## Testing

```bash
pytest
pytest --cov=pq_app --cov-report=term-missing
```

## Docs & Links

- API docs (Swagger): `/api/docs`
- OpenAPI spec: `pq_app/api/openapi.yaml`
- Changelog: `CHANGELOG.md`
- Migrations guide: `MIGRATIONS.md`

## Highlights (Dec 2025)

- Refactored to Blueprint architecture and service layer
- Fully implemented combat system with encounter tracking
- Expanded API with JWT and Swagger documentation

## Contributing & License

- Contributions welcome — open a PR from a feature branch.
- Licensed under MIT — see `LICENSE`.

