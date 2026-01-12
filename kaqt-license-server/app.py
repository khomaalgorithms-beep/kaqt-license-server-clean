import os
import datetime as dt
from flask import Flask, request, jsonify
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


def create_app() -> Flask:
    app = Flask(__name__)

    # Render will provide DATABASE_URL automatically if you attach Postgres
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        # Local fallback (SQLite)
        database_url = "sqlite:///licenses.db"

    # Render postgres URLs start with postgres:// but SQLAlchemy wants postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

    def require_admin():
        token = request.headers.get("X-Admin-Token", "")
        return bool(ADMIN_TOKEN) and token == ADMIN_TOKEN

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True, "service": "kaqt-license-server-clean"})

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

    # ---- ADMIN ----
    @app.get("/admin/list")
    def admin_list():
        if not require_admin():
            return jsonify({"ok": False, "message": "unauthorized"}), 401
        licenses = License.query.order_by(License.created_at.desc()).limit(200).all()
        return jsonify({"ok": True, "data": [l.to_dict() for l in licenses]})

    @app.post("/admin/create")
    def admin_create():
        if not require_admin():
            return jsonify({"ok": False, "message": "unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        license_key = str(data.get("license_key", "")).strip()
        expires_at_str = str(data.get("expires_at", "")).strip()  # ISO format optional

        if not license_key:
            return jsonify({"ok": False, "message": "license_key missing"}), 400

        if License.query.filter_by(license_key=license_key).first():
            return jsonify({"ok": False, "message": "license_key already exists"}), 409

        expires_at = None
        if expires_at_str:
            try:
                expires_at = dt.datetime.fromisoformat(expires_at_str)
            except Exception:
                return jsonify({"ok": False, "message": "expires_at must be ISO format"}), 400

        lic = License(license_key=license_key, expires_at=expires_at, is_active=True)
        db.session.add(lic)
        db.session.commit()

        return jsonify({"ok": True, "data": lic.to_dict()})

    @app.post("/admin/deactivate")
    def admin_deactivate():
        if not require_admin():
            return jsonify({"ok": False, "message": "unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        license_key = str(data.get("license_key", "")).strip()

        lic = License.query.filter_by(license_key=license_key).first()
        if not lic:
            return jsonify({"ok": False, "message": "not found"}), 404

        lic.is_active = False
        db.session.commit()
        return jsonify({"ok": True, "message": "deactivated", "data": lic.to_dict()})

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=True)