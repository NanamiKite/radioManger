"""Loopback-only packaged server with persistent local secrets and safe SPA files."""
import os
from pathlib import Path
import secrets
import sys

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
package_dir = backend_dir.parent if (backend_dir / "frontend_dist").is_dir() else backend_dir
os.chdir(package_dir)


def ensure_local_secret():
    """Generate once, before importing any module that constructs Settings."""
    from dotenv import dotenv_values, set_key

    env_path = package_dir / ".env"
    values = dotenv_values(env_path)
    if not os.environ.get("SECRET_KEY") and not values.get("SECRET_KEY"):
        env_path.touch(mode=0o600, exist_ok=True)
        set_key(str(env_path), "SECRET_KEY", secrets.token_hex(32))
        env_path.chmod(0o600)


ensure_local_secret()

from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app.scripts.init_db import init_database

init_database()

from app.main import app as application


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        prefix = path.split("/", 1)[0]
        if prefix in {"api", "assets", "docs", "redoc", "openapi.json", "health"}:
            if prefix != "assets":
                raise HTTPException(status_code=404)
            return await super().get_response(path, scope)
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or scope["method"] not in {"GET", "HEAD"}:
                raise
            # StaticFiles safely resolves actual files; only extensionless SPA routes fall back.
            if ".." in path.replace("\\", "/").split("/") or Path(path).suffix:
                raise
            return await super().get_response("index.html", scope)


frontend_dist = backend_dir / "frontend_dist"
if frontend_dist.is_dir():
    application.router.routes = [
        route for route in application.router.routes if getattr(route, "name", None) != "root"
    ]
    application.mount("/", SPAStaticFiles(directory=str(frontend_dist)), name="frontend")


if __name__ == "__main__":
    import uvicorn

    print("RadioManager: http://127.0.0.1:8000 — register an account on first use")
    uvicorn.run(application, host="127.0.0.1", port=8000)
