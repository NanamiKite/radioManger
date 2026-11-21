#!/usr/bin/env python3
"""Exercise extracted local packages; never mutate the distributable archive."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile


URL = "http://127.0.0.1:8000"


def extract(archive, destination):
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (destination / member.filename).resolve()
                if not target.is_relative_to(destination) or stat.S_ISLNK(member.external_attr >> 16):
                    raise RuntimeError(f"Unsafe archive member: {member.filename}")
            bundle.extractall(destination)
    elif archive.name.endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as bundle:
            # Packages contain regular files/directories, not links or devices.
            for member in bundle.getmembers():
                if not (member.isfile() or member.isdir()):
                    raise RuntimeError(f"Unsafe archive member: {member.name}")
            bundle.extractall(destination, filter="data")
    else:
        raise RuntimeError("Expected a .zip or .tar.gz package")
    roots = list(destination.iterdir())
    if len(roots) != 1 or not roots[0].is_dir():
        raise RuntimeError("Expected exactly one package directory")
    return roots[0]


def stop(process):
    if os.name == "nt":
        # Kill descendants too, including a server whose launcher failed.
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Could not stop packaged server") from exc


def ready(process, timeout=600):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Packaged server exited with code {process.returncode}")
        try:
            with urllib.request.urlopen(URL + "/health", timeout=2) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    raise RuntimeError("Packaged server did not become healthy; see server logs")


def saved_secret(package):
    for line in (package / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("SECRET_KEY="):
            value = line.partition("=")[2].strip().strip("'\"")
            if len(value) < 32:
                break
            return value
    raise RuntimeError("Packaged server did not persist a strong SECRET_KEY")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--logs", type=Path, required=True)
    args = parser.parse_args()
    archive = args.archive.resolve(strict=True)
    logs = args.logs.resolve()
    logs.mkdir(parents=True, exist_ok=True)
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    manifest = {
        "archive": archive.name,
        "sha256": digest,
        "commit": os.environ.get("GITHUB_SHA", ""),
        "version": args.version,
        "os": platform.system(),
        "arch": platform.machine(),
        "backend_smoke": "failed",
        "gui": "unverified" if "desktop" in archive.name else "not applicable",
    }
    manifest_path = logs / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    shared_smoke = Path(__file__).resolve().with_name("smoke-http.py")
    if not shared_smoke.is_file():
        raise RuntimeError("Missing shared scripts/ci/smoke-http.py")
    # Never accidentally validate another process already running on the runner.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 8000))
    with tempfile.TemporaryDirectory(prefix="radiomanager-smoke-") as temporary:
        work = Path(temporary).resolve()
        extraction = work / "extracted"
        extraction.mkdir()
        package = extract(archive, extraction)
        home = work / "home"
        home.mkdir()
        runtime_temp = work / "tmp"
        runtime_temp.mkdir()
        env = os.environ.copy()
        for key in ("SECRET_KEY", "DATABASE_URL", "DATABASE_MODE", "SQLITE_URL", "SQLITE_PATH",
                    "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "ADMIN_PASSWORD",
                    "LOG_FILE", "UPLOAD_DIR", "UDP_ENABLED"):
            env.pop(key, None)
        env.update(HOME=str(home), USERPROFILE=str(home), XDG_CONFIG_HOME=str(home / ".config"),
                   XDG_DATA_HOME=str(home / ".local"), DATABASE_MODE="sqlite",
                   SQLITE_URL="sqlite:///./radiomanager.db", UDP_ENABLED="false",
                   PYTHONNOUSERSITE="1", PYTHONUNBUFFERED="1")
        env.update(APPDATA=str(home / "AppData" / "Roaming"),
                   LOCALAPPDATA=str(home / "AppData" / "Local"),
                   PIP_CACHE_DIR=str(work / "pip-cache"),
                   TMPDIR=str(runtime_temp), TMP=str(runtime_temp), TEMP=str(runtime_temp))
        desktop = (package / "backend" / "desktop_launcher.py").is_file()
        if os.name == "nt":
            runtime = package / "python" / "python.exe"
            if not runtime.is_file():
                raise RuntimeError("Windows archive has no packaged Python runtime")
            command = [str(runtime), str(package / "backend" / "release_server.py")]
        elif sys.platform == "darwin":
            launcher = package / "start.sh"
            if not launcher.is_file():
                raise RuntimeError("macOS archive has no start.sh")
            # Exercise the actual venv creation, dependency install and startup path.
            command = ["/bin/bash", str(launcher)]
            runtime = package / "venv" / "bin" / "python"
        else:
            raise RuntimeError("Run Windows packages on Windows and macOS packages on macOS")
        state = work / "http-state.json"
        secret = None
        for iteration in (1, 2):
            with (logs / f"server-{iteration}.log").open("w", encoding="utf-8") as output:
                process = subprocess.Popen(command, cwd=package, env=env, stdout=output,
                                           stderr=subprocess.STDOUT, start_new_session=os.name != "nt")
                try:
                    ready(process)
                    persisted = saved_secret(package)
                    if secret is not None and persisted != secret:
                        raise RuntimeError("SECRET_KEY changed after package restart")
                    secret = persisted
                    # This import uses only the package's runtime and bundled backend.
                    version_code = ("import sys; sys.path.insert(0, sys.argv[1]); "
                                    "from app import __version__; "
                                    "assert __version__ == sys.argv[2], (__version__, sys.argv[2]); "
                                    "print('Backend version:', __version__)")
                    if desktop:
                        version_code += ("; from importlib.metadata import version; "
                                         "assert version('pywebview') == '6.2.1'; "
                                         "print('Desktop package metadata verified; GUI NOT exercised')")
                    subprocess.run([str(runtime), "-c", version_code, str(package / "backend"),
                                    args.version], cwd=package, env=env, stdout=output,
                                   stderr=subprocess.STDOUT, check=True, timeout=60)
                    smoke_command = [sys.executable, str(shared_smoke), "--url", URL,
                                     "--mode", "sqlite", "--version", args.version,
                                     "--state" if iteration == 1 else "--verify-state", str(state)]
                    with (logs / f"http-{iteration}.log").open("w", encoding="utf-8") as http_log:
                        subprocess.run(smoke_command, env=env, stdout=http_log,
                                       stderr=subprocess.STDOUT, check=True, timeout=180)
                    if process.poll() is not None:
                        raise RuntimeError("Packaged server exited during HTTP checks")
                finally:
                    stop(process)
        summary = {"archive": archive.name, "version": args.version, "restarts": 1,
                   "database": "sqlite", "secret_persisted": True,
                   "gui": "not exercised" if desktop else "not applicable"}
        (logs / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        manifest["backend_smoke"] = "passed"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary))


if __name__ == "__main__":
    main()
