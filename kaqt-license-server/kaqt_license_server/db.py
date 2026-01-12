from __future__ import annotations

import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_database_uri() -> str:
    """
    Render provides Postgres as DATABASE_URL.
    If not set (local), fallback to SQLite file.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        # Render sometimes gives postgres://, SQLAlchemy prefers postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # Local fallback
    return "sqlite:///licenses.db"