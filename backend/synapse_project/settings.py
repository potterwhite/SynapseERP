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
    # Synapse apps
    "synapse_api",
    "synapse_dashboard",
    "synapse_attendance",
    "synapse_bom_analyzer",
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
        "DIRS": [],
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
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
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
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# --- Custom Project Settings ---

# --- CRITICAL CHANGE ---
# This variable is now OPTIONAL. If not set in .env, it will be None.
ATTENDANCE_ANALYZER_RULE_URL = get_env_variable(
    "ATTENDANCE_ANALYZER_RULE_URL", default=None, is_required=False
)

SYNAPSE_MODULES = [
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
    },
}
