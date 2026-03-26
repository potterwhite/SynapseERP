#!/bin/bash
# SynapseERP — Docker entrypoint for the backend (Django/Gunicorn) container.
#
# Execution order:
#   1. Wait for PostgreSQL to accept connections (TCP probe, pure Python)
#   2. Run Django database migrations
#   3. Collect static files (Django admin CSS/JS → shared volume for Nginx)
#   4. Start Gunicorn
set -e

# --- Step 1: Wait for PostgreSQL ---
# Only needed when DB_ENGINE is PostgreSQL (not SQLite dev mode).
if [ "${DB_ENGINE:-}" = "django.db.backends.postgresql" ]; then
    echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST:-postgres}:${DB_PORT:-5432}..."
    python - <<'PYEOF'
import socket, time, os, sys

host = os.environ.get("DB_HOST", "postgres")
port = int(os.environ.get("DB_PORT", 5432))
for attempt in range(1, 31):
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"[entrypoint] PostgreSQL ready (attempt {attempt}).")
            sys.exit(0)
    except OSError:
        print(f"[entrypoint] Attempt {attempt}/30 — retrying in 2s...")
        time.sleep(2)
print("[entrypoint] ERROR: PostgreSQL not available after 60s. Aborting.")
sys.exit(1)
PYEOF
fi

# --- Step 2: Run migrations ---
cd /app/backend
echo "[entrypoint] Running Django migrations..."
python manage.py migrate --noinput

# --- Step 3: Collect static files ---
# Writes to /app/backend/staticfiles, which is mounted as a shared Docker volume.
# Nginx reads from the same volume at /app/staticfiles (read-only).
echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput --clear

# --- Step 4: Start Gunicorn ---
echo "[entrypoint] Starting Gunicorn with ${GUNICORN_WORKERS:-3} workers..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --access-logfile - \
    --error-logfile - \
    synapse_project.wsgi:application
