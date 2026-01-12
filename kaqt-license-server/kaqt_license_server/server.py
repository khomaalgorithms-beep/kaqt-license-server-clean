<<<<<<< HEAD
from __future__ import annotations

import os
import datetime as dt
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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


def get_database_uri() -> str:
    # Render Postgres provides DATABASE_URL
    url = os.getenv("DATABASE_URL", "").strip()

    # If no database is set, fallback to SQLite file (still works on Render)
    if not url:
        return "sqlite:///licenses.db"

    # Some providers give postgres:// which SQLAlchemy wants as postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


def create_app() -> Flask:
    app = Flask(__name__)

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

        if lic.device_id != device_id:
            return jsonify({
                "ok": False,
                "message": "Device mismatch. License already bound to another device.",
                "bound_device_id": lic.device_id,
            }), 403

        return jsonify({"ok": True, "message": "License valid", "data": lic.to_dict()})

    # Admin endpoints (token required)
    def admin_ok(req) -> bool:
        admin_token = os.getenv("ADMIN_TOKEN", "").strip()
        if not admin_token:
            return False
        return req.headers.get("X-Admin-Token", "") == admin_token

    @app.get("/admin/list")
    def admin_list():
        if not admin_ok(request):
            return jsonify({"ok": False, "message": "Unauthorized"}), 401

        rows = License.query.order_by(License.created_at.desc()).all()
        return jsonify({"ok": True, "count": len(rows), "licenses": [r.to_dict() for r in rows]})

    @app.post("/admin/create")
    def admin_create():
        if not admin_ok(request):
            return jsonify({"ok": False, "message": "Unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        license_key = str(data.get("license_key", "")).strip()
        expires_at = data.get("expires_at")

        if not license_key:
            return jsonify({"ok": False, "message": "license_key missing"}), 400

        existing = License.query.filter_by(license_key=license_key).first()
        if existing:
            return jsonify({"ok": False, "message": "License already exists"}), 409

        exp_dt = None
        if expires_at:
            try:
                exp_dt = dt.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            except Exception:
                return jsonify({"ok": False, "message": "expires_at must be ISO format"}), 400

        lic = License(license_key=license_key, expires_at=exp_dt, is_active=True)
        db.session.add(lic)
        db.session.commit()

        return jsonify({"ok": True, "license": lic.to_dict()}), 201

    return app


app = create_app()
=======
from __future__ import annotations

import os
import datetime as dt
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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


def get_database_uri() -> str:
    # Render Postgres provides DATABASE_URL
    url = os.getenv("DATABASE_URL", "").strip()

    # If no database is set, fallback to SQLite file (still works on Render)
    if not url:
        return "sqlite:///licenses.db"

    # Some providers give postgres:// which SQLAlchemy wants as postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


def create_app() -> Flask:
    app = Flask(__name__)

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

        if lic.device_id != device_id:
            return jsonify({
                "ok": False,
                "message": "Device mismatch. License already bound to another device.",
                "bound_device_id": lic.device_id,
            }), 403

        return jsonify({"ok": True, "message": "License valid", "data": lic.to_dict()})

    # Admin endpoints (token required)
    def admin_ok(req) -> bool:
        admin_token = os.getenv("ADMIN_TOKEN", "").strip()
        if not admin_token:
            return False
        return req.headers.get("X-Admin-Token", "") == admin_token

    @app.get("/admin/list")
    def admin_list():
        if not admin_ok(request):
            return jsonify({"ok": False, "message": "Unauthorized"}), 401

        rows = License.query.order_by(License.created_at.desc()).all()
        return jsonify({"ok": True, "count": len(rows), "licenses": [r.to_dict() for r in rows]})

    @app.post("/admin/create")
    def admin_create():
        if not admin_ok(request):
            return jsonify({"ok": False, "message": "Unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        license_key = str(data.get("license_key", "")).strip()
        expires_at = data.get("expires_at")

        if not license_key:
            return jsonify({"ok": False, "message": "license_key missing"}), 400

        existing = License.query.filter_by(license_key=license_key).first()
        if existing:
            return jsonify({"ok": False, "message": "License already exists"}), 409

        exp_dt = None
        if expires_at:
            try:
                exp_dt = dt.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            except Exception:
                return jsonify({"ok": False, "message": "expires_at must be ISO format"}), 400

        lic = License(license_key=license_key, expires_at=exp_dt, is_active=True)
        db.session.add(lic)
        db.session.commit()

        return jsonify({"ok": True, "license": lic.to_dict()}), 201

    return app


app = create_app()
>>>>>>> b7d674f6 (Pin Python to 3.11 for Render)
