import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = "dummy"
INSTALLED_APPS = [
    "django.contrib.contenttypes",  # required
    "django.contrib.auth",          # often required
    "django_document_manager",                      # your standalone app
]
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
}
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"