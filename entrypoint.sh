#!/usr/bin/env bash
set -e

# Entry point: ensure DB schema exists and run Alembic migrations before starting the app.
echo "Entry point: inspecting DATABASE_URL"

# Normalize DATABASE_URL env var into DB_URL
DB_URL=${DATABASE_URL:-}

echo "Preparing database (if needed) and running alembic upgrade head..."

# If using SQLite and the DB file doesn't exist, create baseline schema using the Flask app factory
if echo "$DB_URL" | grep -qE '^sqlite:'; then
  dbpath=$(python - <<PY
import os
dburl = os.environ.get('DATABASE_URL','')
if dburl.startswith('sqlite:'):
    # return the path portion (may have leading slashes)
    print(dburl.split('sqlite:')[-1])
else:
    print('')
PY
)

  if [ -n "$dbpath" ]; then
    if [ ! -f "$dbpath" ]; then
      echo "SQLite DB file not found at $dbpath - creating baseline schema via Flask app..."
      export APP_ENV=development
      export DATABASE_URL
      python - <<PY
import os
os.environ.setdefault('APP_ENV', 'development')
os.environ.setdefault('DATABASE_URL', os.environ.get('DATABASE_URL',''))
from pq_app import create_app
create_app()
print('Baseline schema created')
PY
    fi
  fi
fi

# Run Alembic migrations with retries
tries=0
until alembic upgrade head; do
  tries=$((tries+1))
  echo "alembic upgrade head failed - waiting and retrying ($tries/30)..."
  if [ $tries -ge 30 ]; then
    echo "alembic upgrade failed after multiple attempts" >&2
    exit 1
  fi
  sleep 2
done
echo "Alembic migrations applied successfully."

# Start the app
if command -v gunicorn >/dev/null 2>&1; then
  echo "Starting gunicorn..."
  exec gunicorn -b 0.0.0.0:5000 run:app
else
  echo "gunicorn not found; starting Flask dev server"
  exec flask run --host=0.0.0.0 --port=5000
fi
