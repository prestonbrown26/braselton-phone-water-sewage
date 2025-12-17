"""Django settings for Braselton utilities voice agent."""

from __future__ import annotations

from pathlib import Path

import environ
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "dev-secret-key"),
    ALLOWED_HOSTS=(list, ["*"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    SESSION_COOKIE_SECURE=(bool, True),
    EMAIL_STUB_MODE=(bool, False),
    LOG_RETENTION_DAYS=(int, 1825),  # 5 years
    TRANSFER_NUMBERS=(list, []),
)

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS: list[str] = env.list("ALLOWED_HOSTS", default=["*"])
CSRF_TRUSTED_ORIGINS: list[str] = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "braselton_django.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "braselton_django.wsgi.application"
ASGI_APPLICATION = "braselton_django.asgi.application"

DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'dev.db'}")}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"

# Session / cookie security
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Proxy / HTTPS security (behind Nginx or a load balancer)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Redirect HTTP -> HTTPS (ONLY turn on once HTTPS is working)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)

# HSTS (start low, increase later once confirmed)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)


# SMTP2Go configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("SMTP2GO_SMTP_HOST", default="smtp.smtp2go.com")
EMAIL_PORT = env.int("SMTP2GO_SMTP_PORT", default=587)
EMAIL_HOST_USER = env("SMTP2GO_USERNAME", default="")
EMAIL_HOST_PASSWORD = env("SMTP2GO_PASSWORD", default="")
EMAIL_USE_TLS = True
EMAIL_FROM_ADDRESS = env("EMAIL_FROM_ADDRESS", default="utilitybilling@braselton.net")
EMAIL_STUB_MODE = env("EMAIL_STUB_MODE")

# Retell / webhook configuration
RETELL_API_KEY = env("RETELL_API_KEY", default="")
WEBHOOK_SHARED_SECRET = env("WEBHOOK_SHARED_SECRET", default="")

# App-specific settings
LOG_RETENTION_DAYS = env("LOG_RETENTION_DAYS")
TOWN_WEBSITE_URL = env("TOWN_WEBSITE_URL", default="https://braselton.net")
AGENT_PHONE_NUMBER = env("AGENT_PHONE_NUMBER", default="Not yet assigned")
TRANSFER_NUMBERS: list[str] = env.list("TRANSFER_NUMBERS", default=[])

# Logging
LOG_LEVEL = env("LOG_LEVEL", default="INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s %(name)s - %(message)s"},
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s [%(filename)s:%(lineno)d] - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

