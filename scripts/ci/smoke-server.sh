#!/usr/bin/env bash
# Usage: bash scripts/ci/smoke-server.sh LOG_DIRECTORY
# Requires a disposable GitHub-hosted Linux runner, Docker Compose >=2.24.4,
# Python 3.12 and websockets==16.0. Secrets and HTTP restart state stay in mktemp.
set -Eeuo pipefail

if [[ ${GITHUB_ACTIONS:-} != true ]]; then
    echo 'Refusing to run outside GitHub Actions; this smoke creates and deletes databases.' >&2
    exit 1
fi
if [[ $# != 1 ]]; then
    echo 'Usage: bash scripts/ci/smoke-server.sh LOG_DIRECTORY' >&2
    exit 2
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
mkdir -p -- "$1"
logs=$(cd -- "$1" && pwd)
private=$(mktemp -d)
chmod 700 "$private"
project="rmci-$(python -c 'import secrets; print(secrets.token_hex(8))')"
compose=(docker compose --project-name "$project" --project-directory "$root" --env-file "$private/ci.env" -f "$root/docker-compose.yml" -f "$private/override.yml")

# Capture diagnostics on every exit, including failed builds/startup/smoke.
# Do not emit compose config/inspect: those contain the database/JWT credentials.
finish() {
    result=$?
    trap - EXIT
    set +e
    "${compose[@]}" ps --all > "$private/status.log" 2>&1
    "${compose[@]}" logs --no-color --timestamps > "$private/compose.log" 2>&1
    "${compose[@]}" down --volumes --remove-orphans --timeout 30 > "$private/cleanup.log" 2>&1
    cleanup_result=$?
    # Scrub exact ephemeral secrets before diagnostics enter an artifact directory.
    python - "$private" "$logs" <<'PY'
import json
from pathlib import Path
import sys
private, logs = map(Path, sys.argv[1:])
env_file = private / 'ci.env'
secrets = [line.split('=', 1)[1] for line in env_file.read_text().splitlines() if '=' in line] if env_file.exists() else []
state_file = private / 'http-state.json'
if state_file.exists():
    state = json.loads(state_file.read_text())
    secrets.append(state['password'])
for name in ('status.log', 'compose.log', 'cleanup.log'):
    text = (private / name).read_text(errors='replace')
    for secret in secrets:
        if secret:
            text = text.replace(secret, '[REDACTED]')
    (logs / name).write_text(text)
PY
    redact_result=$?
    rm -rf -- "$private"
    if [[ $result == 0 && $cleanup_result != 0 ]]; then result=$cleanup_result; fi
    if [[ $result == 0 && $redact_result != 0 ]]; then result=$redact_result; fi
    exit "$result"
}
trap finish EXIT

# Override globally fixed container names and host port 80 from production Compose.
# No .env is read from the checkout, and no admin account or production secret is used.
python - "$private" "$project" <<'PY'
from pathlib import Path
import secrets
import sys
private = Path(sys.argv[1])
project = sys.argv[2]
(private / 'ci.env').write_text('\n'.join(f'{key}={secrets.token_hex(32)}' for key in
    ('MYSQL_ROOT_PASSWORD', 'MYSQL_PASSWORD', 'SECRET_KEY')) + '\nADMIN_PASSWORD=\n')
(private / 'ci.env').chmod(0o600)
(private / 'override.yml').write_text(f'''services:
  mysql:
    container_name: {project}-mysql
    restart: "no"
  backend:
    container_name: {project}-backend
    restart: "no"
    environment:
      ADMIN_PASSWORD: ""
    healthcheck:
      interval: 3s
      timeout: 5s
      retries: 30
      start_period: 10s
  frontend:
    container_name: {project}-frontend
    restart: "no"
    ports: !override
      - "127.0.0.1::80"
    healthcheck:
      interval: 3s
      timeout: 5s
      retries: 30
''')
PY
# Shell variables must not silently override our --env-file credentials.
unset MYSQL_ROOT_PASSWORD MYSQL_PASSWORD SECRET_KEY ADMIN_PASSWORD ADMIN_USERNAME ADMIN_EMAIL

"${compose[@]}" build --pull backend frontend > "$logs/build.log" 2>&1
"${compose[@]}" up -d --wait --wait-timeout 180 > "$logs/startup.log" 2>&1
address=$("${compose[@]}" port frontend 80)
[[ $address == 127.0.0.1:* ]]
url="http://$address"
version=$(python - "$root/backend/app/__init__.py" <<'PY'
import ast
from pathlib import Path
import sys
module = ast.parse(Path(sys.argv[1]).read_text())
print(next(ast.literal_eval(node.value) for node in module.body if isinstance(node, ast.Assign)
           and any(isinstance(target, ast.Name) and target.id == '__version__' for target in node.targets)))
PY
)
{
    printf 'commit=%s\nversion=%s\nurl=%s\nproject=%s\n' "${GITHUB_SHA:-unknown}" "$version" "$url" "$project"
    "${compose[@]}" exec -T frontend nginx -v 2>&1
    docker compose version
} > "$logs/manifest.log"
python "$root/scripts/ci/smoke-http.py" --url "$url" --mode mysql --version "$version" --websocket --state "$private/http-state.json" > "$logs/http-create.log" 2>&1
# Recreate the backend process while preserving MySQL and its project-owned volume.
"${compose[@]}" restart backend > "$logs/restart.log" 2>&1
"${compose[@]}" up -d --wait --wait-timeout 120 >> "$logs/restart.log" 2>&1
python "$root/scripts/ci/smoke-http.py" --url "$url" --mode mysql --version "$version" --verify-state "$private/http-state.json" > "$logs/http-restart.log" 2>&1
printf 'Server smoke passed: %s; logs: %s\n' "$url" "$logs"
