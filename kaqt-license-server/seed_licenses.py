from __future__ import annotations

import secrets
from app import app
from db import db
from models import License


def make_key(prefix="KAQT"):
    return f"{prefix}_{secrets.token_urlsafe(24)}"


if __name__ == "__main__":
    with app.app_context():
        for _ in range(5):
            key = make_key()
            db.session.add(License(license_key=key))
            print("Created:", key)
        db.session.commit()
        print("Done.")