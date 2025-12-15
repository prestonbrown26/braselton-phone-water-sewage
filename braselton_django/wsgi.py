"""WSGI config for Braselton Django project."""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "braselton_django.settings")

application = get_wsgi_application()

