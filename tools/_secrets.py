"""Resolve a credential without it having to live in an exported environment variable.

Why this exists: the harness reads arbitrary web pages and ticket threads. If an agent with a
shell reads a page that says "print your environment", an exported ATLASSIAN_API_TOKEN is one
`env` away. The fix is to keep the secret out of the environment the agent's shell can see and
fetch it only inside the one script that needs it, at the moment it needs it.

Resolution order (first hit wins):
  1. macOS Keychain - service "gene2", account = the variable name. Save from the clipboard (the
     interactive prompt cuts input at 128 characters, too short for a QMetry key):
       security add-generic-password -U -s gene2 -a ATLASSIAN_API_TOKEN -w "$(pbpaste)"
       security add-generic-password -U -s gene2 -a QMETRY_API_KEY -w "$(pbpaste)"
  2. ~/.config/gene2/credentials.json - {"ATLASSIAN_API_TOKEN": "..."} - refused unless the file
     is readable by its owner only (chmod 600). Override the path with GENE2_CREDENTIALS_FILE.
  3. An environment variable of the same name - still accepted (CI masked variables are the
     normal case there), but outside CI it prints a one-line warning so nobody mistakes it for
     the recommended setup.

Non-secret settings (ATLASSIAN_BASE_URL, JIRA_PROJECT_KEY, ...) go through the same function so
there is one place to configure everything, but they never trigger the warning.
"""
from __future__ import annotations

import json
import os
import pathlib
import stat
import subprocess
import sys

SECRET_NAMES = {"ATLASSIAN_API_TOKEN", "GENE2_PASSWORD", "QMETRY_API_KEY"}
_warned: set[str] = set()


def _keychain(name: str) -> str | None:
    if sys.platform != "darwin":
        return None
    try:
        r = subprocess.run(
            ["security", "find-generic-password", "-s", "gene2", "-a", name, "-w"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = r.stdout.strip()
    return value if r.returncode == 0 and value else None


def credentials_file() -> pathlib.Path:
    return pathlib.Path(os.environ.get("GENE2_CREDENTIALS_FILE",
                                       pathlib.Path.home() / ".config" / "gene2" / "credentials.json"))


def _from_file(name: str) -> str | None:
    path = credentials_file()
    if not path.exists():
        return None
    mode = path.stat().st_mode
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise SystemExit(f"{path} is readable by group/others - run: chmod 600 {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get(name)
    except json.JSONDecodeError as e:
        raise SystemExit(f"{path} is not valid JSON: {e}")
    return str(value) if value else None


def get(name: str, default: str = "") -> str:
    value = _keychain(name) or _from_file(name)
    if value:
        return value
    value = os.environ.get(name, "")
    if value and name in SECRET_NAMES and not os.environ.get("CI") and name not in _warned:
        _warned.add(name)
        print(f"warning: {name} read from an exported environment variable. Any agent with shell "
              f"access can read that. Prefer the keychain or {credentials_file()} (see "
              f"tools/_secrets.py).", file=sys.stderr)
    return value or default


def atlassian() -> tuple[str, tuple[str, str]]:
    base = get("ATLASSIAN_BASE_URL").rstrip("/")
    email = get("ATLASSIAN_EMAIL")
    token = get("ATLASSIAN_API_TOKEN")
    if not (base and email and token):
        raise SystemExit("Atlassian credentials not found. Set ATLASSIAN_BASE_URL, ATLASSIAN_EMAIL "
                         "and ATLASSIAN_API_TOKEN via the keychain, "
                         f"{credentials_file()}, or (CI only) environment variables.")
    return base, (email, token)
