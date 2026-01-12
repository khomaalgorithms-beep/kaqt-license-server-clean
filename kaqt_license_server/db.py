from __future__ import annotations

import os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_database_uri() -> str:
    """
    Uses Render's DATABASE_URL if present, otherwise falls back to sqlite.
    Forces psycopg v3 driver: postgresql+psycopg://
    Ensures sslmode=require for Render Postgres.
    """
    raw = (os.getenv("DATABASE_URL") or "").strip()

    if not raw:
        # local fallback
        return "sqlite:///licenses.sqlite3"

    # Render sometimes gives postgres://
    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql+psycopg://", 1)

    # Standard postgresql:// -> use psycopg driver
    if raw.startswith("postgresql://"):
        raw = raw.replace("postgresql://", "postgresql+psycopg://", 1)

    parsed = urlparse(raw)
    qs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    qs.setdefault("sslmode", "require")
    parsed = parsed._replace(query=urlencode(qs))
    return urlunparse(parsed)