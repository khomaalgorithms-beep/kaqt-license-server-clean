from __future__ import annotations

import os
import datetime as dt
from flask import Flask, jsonify, request

from db import db, get_database_uri
from models import License


def _require_admin(req) -> bool:
    # Protect admin endpoints with a secret token
    token = (req.headers.get("X-Admin-Token") or "").strip()
    expected = (os.getenv("ADMIN_TOKEN") or "").strip()
    return bool(expected) and token == expected


def create_app() -> Flask:
    app = Flask(__name__)

    # DB config
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True, "service": "kaqt-license-server"})

    @app.post("/validate")
    def validate():
        data = request.get_json(silent=True) or {}

        license_key = str(data.get("license_key", "")).strip()
        device_id = str(data.get("device_id", "")).strip()

        if not license_key:
            return jsonify({"ok": False, "message": "license_key missing"}), 400
        if not device_id:
            return jsonify({"ok": False, "message": "device_id missing"}), 400

        lic = License.query.filter_by(license_key=license_key).first()
        if not lic:
            return jsonify({"ok": False, "message": "License key not found"}), 404

        if not lic.is_active:
            return jsonify({"ok": False, "message": "License is inactive"}), 403

        if lic.is_expired():
            return jsonify({"ok": False, "message": "License expired"}), 403

        # bind device on first successful validation
        if not lic.device_id:
            lic.device_id = device_id
            db.session.commit()

        # enforce same device forever
        if lic.device_id != device_id:
            return jsonify({
                "ok": False,
                "message": "Device mismatch. License already bound to another device.",
                "bound_device_id": lic.device_id,
            }), 403

        return jsonify({"ok": True, "message": "License valid", "data": lic.to_dict()})

    # -------------------------------
    # ADMIN: Create license keys
    # -------------------------------
    @app.post("/admin/create")
    def admin_create():
        if not _require_admin(request):
            return jsonify({"ok": False, "message": "Unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        license_key = str(data.get("license_key", "")).strip()
        expires_at = data.get("expires_at")  # ISO string or null
        is_active = bool(data.get("is_active", True))

        if not license_key:
            return jsonify({"ok": False, "message": "license_key missing"}), 400

        existing = License.query.filter_by(license_key=license_key).first()
        if existing:
            return jsonify({"ok": False, "message": "license_key already exists"}), 409

        exp_dt = None
        if isinstance(expires_at, str) and expires_at.strip():
            # expects ISO like "2026-12-31T00:00:00"
            exp_dt = dt.datetime.fromisoformat(expires_at.strip())

        lic = License(
            license_key=license_key,
            is_active=is_active,
            expires_at=exp_dt,
        )
        db.session.add(lic)
        db.session.commit()

        return jsonify({"ok": True, "message": "Created", "data": lic.to_dict()})

    @app.get("/admin/list")
    def admin_list():
        if not _require_admin(request):
            return jsonify({"ok": False, "message": "Unauthorized"}), 401

        rows = License.query.order_by(License.id.desc()).limit(200).all()
        return jsonify({"ok": True, "data": [r.to_dict() for r in rows]})

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=True)