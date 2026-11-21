#!/bin/bash
# Migrate the configured database; provision MySQL credentials separately.
set -e
cd "$(dirname "$0")/backend"
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi
exec python -m app.scripts.init_db "$@"
