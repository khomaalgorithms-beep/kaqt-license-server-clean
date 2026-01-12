from __future__ import annotations

import os
from functools import wraps
from flask import request, jsonify


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        expected = os.getenv("ADMIN_TOKEN", "").strip()
        provided = request.headers.get("X-Admin-Token", "").strip()

        if not expected:
            return jsonify({"ok": False, "message": "ADMIN_TOKEN not configured"}), 500

        if provided != expected:
            return jsonify({"ok": False, "message": "Unauthorized"}), 401

        return fn(*args, **kwargs)

    return wrapper