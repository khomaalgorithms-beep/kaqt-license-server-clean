from __future__ import annotations

import os
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def get_database_uri() -> str:
    # Render Postgres gives DATABASE_URL
    url = os.getenv("DATABASE_URL", "").strip()

    if not url:
        # Local fallback (optional)
        # Example: export DATABASE_URL="postgresql://user:pass@localhost:5432/kaqt"
        raise RuntimeError("DATABASE_URL is missing. Set it in Render Environment Variables.")

    # Render uses postgres:// but SQLAlchemy expects postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url