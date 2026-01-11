from __future__ import annotations

import os
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def _normalize_database_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""

    # Render sometimes gives postgres://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)

    # If it's postgresql://, switch to psycopg driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Ensure sslmode=require
    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
    parsed = urlparse(url)
    qs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if "sslmode" not in qs:
        qs["sslmode"] = "require"
    parsed = parsed._replace(query=urlencode(qs))
    return urlunparse(parsed)