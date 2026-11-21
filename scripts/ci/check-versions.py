"""Validate release metadata without importing runtime dependencies or settings."""
import ast
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]


def main():
    module = ast.parse((ROOT / "backend/app/__init__.py").read_text(encoding="utf-8"))
    backend = next(
        ast.literal_eval(statement.value)
        for statement in module.body
        if isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__version__" for target in statement.targets)
    )
    frontend = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    electron = json.loads((ROOT / "frontend/electron/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
    versions = {
        "backend": backend,
        "frontend": frontend["version"],
        "electron": electron["version"],
        "npm lock": lock["version"],
        "npm lock root": lock["packages"][""]["version"],
    }
    for name, version in versions.items():
        print(f"{name}: {version}")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", backend):
        raise SystemExit("Backend release version is not X.Y.Z[-prerelease]")
    if any(version != backend for version in versions.values()):
        raise SystemExit("Project release versions differ")


if __name__ == "__main__":
    main()
