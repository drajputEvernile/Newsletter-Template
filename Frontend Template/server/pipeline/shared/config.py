"""Slim stand-in for backend/pipeline/shared/config.py: only what the email renderer needs.

Settings are read from the process environment, then `server/.env` (optional).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _env_file_values() -> dict[str, str]:
    path = SERVER_DIR / ".env"
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def getenv_optional(name: str, default: str = "") -> str:
    """Resolve *name* from process environment, then `server/.env`."""
    v = os.environ.get(name) or _env_file_values().get(name) or default
    return v.strip() if isinstance(v, str) else default
