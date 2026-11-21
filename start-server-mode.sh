#!/bin/bash
# Configure backend/.env (DATABASE_MODE=mysql and DATABASE_URL) before starting.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/backend"
if [ ! -d venv ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi
export DATABASE_MODE=mysql
mkdir -p logs uploads
python -m app.scripts.init_db
echo "Backend: http://127.0.0.1:8000; register on first use or explicitly create an administrator."
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
