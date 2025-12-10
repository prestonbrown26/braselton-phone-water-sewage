"""Application factory for braselton_ai_agent."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect

# SQLAlchemy instance shared across modules
db = SQLAlchemy()

# Login manager
login_manager = LoginManager()
# CSRF protection
csrf = CSRFProtect()


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
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "true").strip().lower()
        in {"1", "true", "yes", "on"},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=True,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        # Retell AI configuration
        RETELL_API_KEY=os.getenv("RETELL_API_KEY", ""),
        WEBHOOK_SHARED_SECRET=os.getenv("WEBHOOK_SHARED_SECRET", ""),
        # SMTP2Go email configuration
        SMTP2GO_SMTP_HOST=os.getenv("SMTP2GO_SMTP_HOST", "smtp.smtp2go.com"),
        SMTP2GO_SMTP_PORT=int(os.getenv("SMTP2GO_SMTP_PORT", "587")),
        SMTP2GO_USERNAME=os.getenv("SMTP2GO_USERNAME", ""),
        SMTP2GO_PASSWORD=os.getenv("SMTP2GO_PASSWORD", ""),
        EMAIL_FROM_ADDRESS=os.getenv("EMAIL_FROM_ADDRESS", "utilitybilling@braselton.net"),
        EMAIL_STUB_MODE=os.getenv("EMAIL_STUB_MODE", "false").strip().lower()
        in {"1", "true", "yes", "on"},
        # Admin portal credentials
        ADMIN_USERNAME=os.getenv("ADMIN_USERNAME", "admin"),
        ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD", "changeme"),
        # 5-year retention per Georgia state law LG 20-022
        LOG_RETENTION_DAYS=int(os.getenv("LOG_RETENTION_DAYS", "1825")),
        # Town website for email links
        TOWN_WEBSITE_URL=os.getenv("TOWN_WEBSITE_URL", "https://braselton.net"),
        AGENT_PHONE_NUMBER=os.getenv("AGENT_PHONE_NUMBER", "Not yet assigned"),
    )

    transfer_numbers = [
        number.strip()
        for number in os.getenv("TRANSFER_NUMBERS", "").split(",")
        if number.strip()
    ]
    app.config["TRANSFER_NUMBERS"] = transfer_numbers

    configure_logging(app)

    db.init_app(app)
    csrf.init_app(app)
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Please log in to access this page.'

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
    from .health import health_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)


# WSGI entry point expected by gunicorn (``app:app``)
app = create_app()


