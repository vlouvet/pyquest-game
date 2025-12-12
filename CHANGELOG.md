# Changelog

All notable changes to this project are documented here. This project follows a date-based changelog. For migration-specific details, see `MIGRATIONS.md`.

## 2025-12-11

### Added
- Full combat system with `CombatAction` model and encounter tracking.
- Class and race-specific combat abilities (damage, healing, defense mechanics).
- RESTful API with OpenAPI/Swagger docs available at `/api/docs`.
- JWT authentication for API endpoints.
- Service layer pattern: `CombatService`, `TileService`, `MediaService`.
- Comprehensive configuration management across environments.
- CSS styling improvements for better UX.
- Enhanced `User` model with game stats (strength, intelligence, stealth, etc.).
- Alembic migrations and new tables:
  - Add `ActionOption.code` field.
  - Add ON DELETE CASCADE for actions.
  - Make `ActionOption.code` not nullable.
  - Add `Playthrough` model.
  - Add ASCII art to `TileTypeOption`.
  - Add Combat, Encounter, and Media tables.

### Changed
- Refactored to a proper Blueprint architecture; removed duplication between `__init__.py` and `app.py`.
- Improved database models with clearer relationships and helper methods.

### Fixed
- Form validation issues across several flows.
- Consistency bugs between `user_id` and `player_id` usages.

### Security
- Hardened authorization checks for API endpoints.
- Improved secret key management and configuration handling.

### Testing & Quality
- Test suite expanded to 95/96 passing tests (99% pass rate).
- Code coverage at ~77% overall.

---

Older changes are captured in commit history. Future releases will continue using this file for highlights. For schema and API specifics, consult the codebase and Swagger UI.