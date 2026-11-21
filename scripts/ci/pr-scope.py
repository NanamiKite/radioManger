"""Select PR checks from both sides of the Git diff; never call external services."""
import argparse
import os
from pathlib import Path
import subprocess


CHECKS = ("frontend", "backend", "mysql", "scripts", "versions", "workflows")


def select_checks(paths):
    selected = set()
    for path in paths:
        if path.startswith("doc/") or path.lower().endswith(".md"):
            continue
        if path.startswith((".github/", "scripts/ci/")):
            selected.update(("scripts", "versions", "workflows"))
        elif path.startswith("frontend/tests/"):
            # Browser contracts are an explicit manual diagnostic, not a PR gate.
            selected.update(("frontend", "scripts"))
        elif path.startswith("frontend/"):
            selected.add("frontend")
            if path in ("frontend/package.json", "frontend/package-lock.json", "frontend/electron/package.json"):
                selected.add("versions")
            if path in ("frontend/Dockerfile", "frontend/nginx.conf", "frontend/.dockerignore"):
                selected.add("scripts")
        elif path.startswith(("backend/app/", "backend/alembic/")) or path in (
            "backend/requirements.txt", "backend/alembic.ini"
        ):
            selected.update(("backend", "mysql"))
            if path == "backend/app/__init__.py":
                selected.add("versions")
        elif path.startswith("backend/tests/contracts/mysql/"):
            selected.add("mysql")
        elif path.startswith("backend/tests/"):
            selected.add("backend")
            if path in ("backend/tests/conftest.py", "backend/tests/contracts/conftest.py"):
                selected.add("mysql")
        elif path.startswith("backend/"):
            selected.add("backend")
            if path in ("backend/Dockerfile", "backend/.dockerignore"):
                selected.add("scripts")
        elif path.startswith("scripts/") or path.endswith((".sh", ".bat", ".ps1")):
            selected.update(("scripts", "versions"))
        elif path in ("docker-compose.yml", "nginx.conf", ".gitignore"):
            selected.add("scripts")
        else:
            # An unclassified runtime/config file must not silently lose coverage.
            selected.update(CHECKS)
    return {name: name in selected for name in CHECKS}


def changed_paths(base, head):
    # No rename detection: a rename must cover the old AND new directory.
    result = subprocess.run(
        ["git", "diff", "--no-renames", "--name-only", "-z", f"{base}...{head}", "--"],
        check=True, capture_output=True,
    )
    return [os.fsdecode(path) for path in result.stdout.split(b"\0") if path]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    selected = select_checks(changed_paths(args.base, args.head))
    rows = [f"{name}={str(enabled).lower()}" for name, enabled in selected.items()]
    print("\n".join(rows))
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write("\n".join(rows) + "\n")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("## PR check scope\n\n| Check | Selected |\n| --- | --- |\n")
            for name, enabled in selected.items():
                stream.write(f"| {name} | {'yes' if enabled else 'not applicable'} |\n")
            stream.write("\nFull contracts and platform packages run only via the manual workflow.\n")


if __name__ == "__main__":
    main()
