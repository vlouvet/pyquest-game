# Running Alembic Migrations (safe steps)

This project includes Alembic migrations in `alembic/`. Follow these steps to run migrations safely:

1. Backup your database

   Always take a backup/snapshot of your production or development database before running migrations.

2. Set `DATABASE_URL` environment variable

   Alembic in this repo reads the DB URL from `DATABASE_URL`. Export it in your shell:

```fish
set -x DATABASE_URL "postgresql://user:pass@host:5432/dbname"
```

3. Run migrations

```fish
# from repository root
alembic -c alembic.ini upgrade head
```

4. Important notes

- The repository's `create_app()` will not call `db.create_all()` or seed defaults unless `APP_ENV` (or the `config_name` passed into `create_app`) is `development` or `testing`. In production, rely on Alembic.
- Migration `0001` adds the `actionoption.code` column and backfills it from `name`.
- Migration `0002` attempts to replace the `action.tile` foreign key with an `ON DELETE CASCADE` constraint. It inspects the database to find the existing FK name; however, constraint names vary by dialect and environment. Review the generated SQL or run the migration on a staging copy first.
- Migration `0003` makes `actionoption.code` non-nullable. It assumes `0001` backfilled values.

5. If you use SQLite for local tests

- SQLite ignores `FOR UPDATE` locking — row-level locking in the app will be no-op on SQLite but functions correctly on PostgreSQL/MySQL.
- Alembic operations on SQLite have limitations (e.g., altering columns). Prefer testing migrations on a Postgres/MySQL dev DB when possible.

6. Troubleshooting

- If a migration fails due to an unexpected constraint name, inspect the DB (e.g. `
psql -c "\d action"` on Postgres) to find the FK name and adjust the migration accordingly.
- If needed, create a DB dump and restore it to test migrations repeatedly.

If you want, I can also add a small script to run migrations against the app's configured DB URL automatically, or add a CI step to run migrations on a staging DB before deploy.
