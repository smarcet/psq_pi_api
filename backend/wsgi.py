"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(CURRENT_PATH, ".env")
load_dotenv(ENV_FILE)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_wsgi_application()
