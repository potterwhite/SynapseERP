# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.8.0-20250910 (Central project settings for SynapseERP)

import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
import dotenv
from django.utils.translation import gettext_lazy as _

# --- Base Directory ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Environment Variable Loading ---
dotenv.load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_env_variable(var_name, default=None, is_required=False):  # <-- MODIFIED
    """Gets an environment variable. If is_required is True, it must exist."""
    try:
        return os.environ[var_name]
    except KeyError:
        if not is_required:  # <-- MODIFIED
            return default
        error_msg = f'CRITICAL ERROR: The required environment variable "{var_name}" is not set.'
        raise ImproperlyConfigured(error_msg)


# --- Core Security Settings (Loaded from Environment) ---
SECRET_KEY = get_env_variable("DJANGO_SECRET_KEY", is_required=True)  # <-- MODIFIED
DEBUG = get_env_variable("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = get_env_variable("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,192.168.0.19:8000").split(
    ","
)

# In development the Vue SPA runs on :5173 (Vite) and proxies /admin/ to :8000.
# Django's CSRF middleware checks the Origin/Referer header against
# CSRF_TRUSTED_ORIGINS; without this entry the admin login POST from the
# Vite proxy would be rejected as a cross-origin request.
CSRF_TRUSTED_ORIGINS = get_env_variable(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
).split(",")

# --- Application Definitions ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # enables logout/token invalidation
    # Synapse apps
    "synapse_auth",   # Phase 5.7: JWT auth + user roles
    "synapse_api",
    "synapse_dashboard",
    "synapse_attendance",
    "synapse_bom_analyzer",
    "synapse_pm",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "synapse_project.urls"
WSGI_APPLICATION = "synapse_project.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]
def get_db_config() -> dict:
    """
    Build database configuration based on DB_ENGINE environment variable.

    DB_ENGINE=django.db.backends.postgresql  → PostgreSQL (Docker / production)
    DB_ENGINE=django.db.backends.sqlite3     → SQLite (default, local dev)

    PostgreSQL env vars: DB_NAME, DB_USER, DB_PASSWORD (required), DB_HOST, DB_PORT
    """
    engine = get_env_variable("DB_ENGINE", "django.db.backends.sqlite3")

    if engine == "django.db.backends.postgresql":
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": get_env_variable("DB_NAME", "synapse_db"),
                "USER": get_env_variable("DB_USER", "synapse_user"),
                # DB_PASSWORD is required when using PostgreSQL
                "PASSWORD": get_env_variable("DB_PASSWORD", is_required=True),
                "HOST": get_env_variable("DB_HOST", "localhost"),
                "PORT": get_env_variable("DB_PORT", "5432"),
                # Keep connections alive for 10 min (matches Gunicorn worker lifespan)
                "CONN_MAX_AGE": 600,
                "OPTIONS": {"connect_timeout": 10},
            }
        }

    # Default: SQLite for local development — no credentials required
    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


DATABASES = get_db_config()
LANGUAGE_CODE = "zh-hans"
LANGUAGES = [
    ("en", "English"),
    ("zh-hans", "Simplified Chinese"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    # Phase 5.7: JWT is the primary auth method.
    # SessionAuthentication is kept for /admin/ Django admin compatibility.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# --- JWT Settings (Phase 5.7) ---
from datetime import timedelta
SIMPLE_JWT = {
    # Access token expires quickly to limit exposure window
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    # Refresh token is long-lived; rotated on every use
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Rotating refresh tokens: every refresh call issues a new refresh token
    # and blacklists the old one. Requires token_blacklist app.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    # Standard Bearer token scheme
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    # Include user_id and username in the token for debugging
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- Custom Project Settings ---

# --- CRITICAL CHANGE ---
# This variable is now OPTIONAL. If not set in .env, it will be None.
ATTENDANCE_ANALYZER_RULE_URL = get_env_variable(
    "ATTENDANCE_ANALYZER_RULE_URL", default=None, is_required=False
)

# --- Project Management (DB-Primary since Phase 5.2) ---
# The database is always the source of truth for PM data.
# Obsidian vault sync is an optional feature controlled by these settings.

# OBSIDIAN_VAULT_PATH: absolute path to the Obsidian vault root directory.
# Required only if you want to sync data between DB and Obsidian.
OBSIDIAN_VAULT_PATH = get_env_variable("OBSIDIAN_VAULT_PATH", default=None)

# OBSIDIAN_SYNC_ENABLED: set to 'True' to enable vault sync features.
# Defaults to True if OBSIDIAN_VAULT_PATH is set, False otherwise.
_sync_enabled_raw = get_env_variable("OBSIDIAN_SYNC_ENABLED", default=None)
if _sync_enabled_raw is not None:
    OBSIDIAN_SYNC_ENABLED = _sync_enabled_raw.lower() in ("true", "1", "yes")
else:
    OBSIDIAN_SYNC_ENABLED = bool(OBSIDIAN_VAULT_PATH)

# Warn at startup if sync is enabled but the vault path is missing or invalid.
import logging as _logging
_pm_log = _logging.getLogger("synapse_pm")
if OBSIDIAN_SYNC_ENABLED:
    if not OBSIDIAN_VAULT_PATH:
        _pm_log.warning(
            "OBSIDIAN_SYNC_ENABLED is True but OBSIDIAN_VAULT_PATH is not set in .env. "
            "Vault sync will not work until a valid vault path is provided."
        )
    else:
        import os as _os
        if not _os.path.isdir(OBSIDIAN_VAULT_PATH):
            _pm_log.warning(
                "OBSIDIAN_VAULT_PATH '%s' does not exist or is not a directory. "
                "Vault sync will not work until the path is corrected.",
                OBSIDIAN_VAULT_PATH,
            )

SYNAPSE_MODULES = [
    {
        "app_name": "synapse_pm",
        "display_name": _("Project Management"),
        "url_name": "pm",
        "description": _("Manage projects and tasks with Obsidian vault integration."),
        "placement": "toolbox",
        "order": 5,
    },
    {
        "app_name": "synapse_attendance",
        "display_name": _("Attendance Analyzer"),
        "url_name": "synapse_attendance:analyze",
        "description": _("Analyze employee punch card data."),
        "placement": "toolbox",
        "order": 10,
    },
    {
        "app_name": "synapse_bom_analyzer",
        "display_name": _("BOM Analyzer"),
        "url_name": "synapse_bom_analyzer:analyze",
        "description": _("Aggregate materials from multiple BOM files."),
        "placement": "toolbox",
        "order": 20,
    },
]

# --- LOGGING CONFIGURATION ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "synapse_dashboard": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "synapse_attendance": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "synapse_bom_analyzer": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "synapse_pm": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
