"""Application factory for braselton_ai_agent."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy instance shared across modules
db = SQLAlchemy()


def create_app() -> Flask:
    """Flask application factory.

    Loads configuration from environment variables and registers blueprints.
    """

    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)  # Safe to call multiple times; no-op if file missing.

    app = Flask(__name__)

    # Default configuration with environment overrides
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///dev.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        LIVEKIT_URL=os.getenv("LIVEKIT_URL", ""),
        LIVEKIT_API_KEY=os.getenv("LIVEKIT_API_KEY", ""),
        LIVEKIT_API_SECRET=os.getenv("LIVEKIT_API_SECRET", ""),
        OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
        SMTP2GO_API_KEY=os.getenv("SMTP2GO_API_KEY", ""),
        SMTP2GO_SMTP_HOST=os.getenv("SMTP2GO_SMTP_HOST", "smtp.smtp2go.com"),
        SMTP2GO_SMTP_PORT=int(os.getenv("SMTP2GO_SMTP_PORT", "587")),
        SMTP2GO_USERNAME=os.getenv("SMTP2GO_USERNAME", ""),
        SMTP2GO_PASSWORD=os.getenv("SMTP2GO_PASSWORD", ""),
        TEAMS_WEBHOOK_URL=os.getenv("TEAMS_WEBHOOK_URL", ""),
        ADMIN_USERNAME=os.getenv("ADMIN_USERNAME", "admin"),
        ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD", "changeme"),
        LOG_RETENTION_DAYS=int(os.getenv("LOG_RETENTION_DAYS", "1825")),  # 5 years
    )

    configure_logging(app)

    db.init_app(app)

    register_blueprints(app)

    with app.app_context():
        # In production, use migrations instead of create_all.
        if os.getenv("FLASK_ENV") == "development":
            db.create_all()

    return app


def configure_logging(app: Flask) -> None:
    """Configure basic logging for the application."""

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""

    from .routes import main_bp
    from .admin import admin_bp
    from .monitor import monitor_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(monitor_bp)


# WSGI entry point expected by gunicorn (``app:app``)
app = create_app()


