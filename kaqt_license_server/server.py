from __future__ import annotations

import os
import datetime as dt
from flask import Flask, jsonify, request

from kaqt_license_server.db import db, get_database_uri


class License(db.Model):
    __tablename__ = "licenses"

    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    device_id = db.Column(db.String(128), nullable=True, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return dt.datetime.utcnow() > self.expires_at

    def to_dict(self):
        return {
            "license_key": self.license_key,
            "device_id": self.device_id,
            "is_active": bool(self.is_active),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    def _admin_ok(req) -> bool:
        token = os.getenv("ADMIN_TOKEN", "").strip()
        return bool(token) and req.headers.get("X-Admin-Token", "") == token

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

        if not lic.device_id:
            lic.device_id = device_id
            db.session.commit()

        if lic.device_id != device_id:
            return jsonify({
                "ok": False,
                "message": "Device mismatch. License already bound to another device.",
                "bound_device_id": lic.device_id,
            }), 403

        return jsonify({"ok": True, "message": "License valid", "data": lic.to_dict()})

    # ---- ADMIN endpoints (protected) ----
    @app.post("/admin/create")
    def admin_create():
        if not _admin_ok(request):
            return jsonify({"ok": False, "message": "Unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        license_key = str(data.get("license_key", "")).strip()
        expires_at = data.get("expires_at")  # iso string optional

        if not license_key:
            return jsonify({"ok": False, "message": "license_key missing"}), 400

        existing = License.query.filter_by(license_key=license_key).first()
        if existing:
            return jsonify({"ok": False, "message": "Already exists"}), 409

        exp_dt = None
        if expires_at:
            exp_dt = dt.datetime.fromisoformat(expires_at)

        lic = License(license_key=license_key, expires_at=exp_dt, is_active=True)
        db.session.add(lic)
        db.session.commit()
        return jsonify({"ok": True, "data": lic.to_dict()})

    @app.get("/admin/list")
    def admin_list():
        if not _admin_ok(request):
            return jsonify({"ok": False, "message": "Unauthorized"}), 401

        rows = License.query.order_by(License.created_at.desc()).limit(200).all()
        return jsonify({"ok": True, "data": [r.to_dict() for r in rows]})

    return app


app = create_app()