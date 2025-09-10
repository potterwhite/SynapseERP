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

# --- Base Directory ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Environment Variable Loading ---
# This will load the .env file from the project root (BASE_DIR).
# The .env file is NOT version controlled and is specific to each deployment.
dotenv.load_dotenv(os.path.join(BASE_DIR, '.env'))

def get_env_variable(var_name, default=None):
    """Gets an environment variable. If default is not provided, it's required."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        error_msg = f'CRITICAL ERROR: The required environment variable "{var_name}" is not set.'
        raise ImproperlyConfigured(error_msg)

# --- Core Security Settings (Loaded from Environment) ---
# The run.sh script will generate a .env file with these values for development.
# In production, these should be set as true environment variables on the server.

# SECRET_KEY is mandatory for cryptographic signing.
SECRET_KEY = get_env_variable('DJANGO_SECRET_KEY')

# DEBUG mode should always be False in production.
DEBUG = get_env_variable('DJANGO_DEBUG', 'False') == 'True'

# A comma-separated list of allowed hosts.
ALLOWED_HOSTS = get_env_variable('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# --- Application Definitions ---
INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Synapse Framework Apps
    'synapse_dashboard',
    'synapse_attendance',
    'synapse_bom_analyzer',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'synapse_project.urls'  # UPDATED to point to our new project urls

WSGI_APPLICATION = 'synapse_project.wsgi.application' # UPDATED

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # CORRECTED: This was pointing to LocaleMiddleware by mistake.
                # It should point to the i18n context processor.
                'django.template.context_processors.i18n',
            ],
        },
    },
]

# --- Database ---
# By default, uses a simple SQLite database file in the project root.
# For production, this can be overridden with environment variables for PostgreSQL, etc.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- Internationalization (i18n) & Localization (l10n) ---
LANGUAGE_CODE = 'zh-hans'
LANGUAGES = [
    ('en', 'English'),
    ('zh-hans', 'Simplified Chinese'),
]
LOCALE_PATHS = [ BASE_DIR / 'locale' ]
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static Files ---
# These settings are for managing CSS, JavaScript, and images.
STATIC_URL = '/static/'
# This is where `collectstatic` will gather all static files for deployment.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# --- Default primary key field type ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Custom Project Settings ---
# These are settings specific to your application's logic.

# NOTE: Custom settings that change frequently or are environment-specific
# should also be loaded from environment variables for best practice.
ATTENDANCE_ANALYZER_RULE_URL = get_env_variable(
    'ATTENDANCE_ANALYZER_RULE_URL',
    'https://gist.githubusercontent.com/MrJamesLZA/76c4bc7a67dc386c7205ac191bc04eae/raw/74cb2717cf6c3998d7d7348d8a6d93bddb31bceb/attendance-rule-baytto.toml'
)

# This setting has been removed as part of the simplification/refactoring.
# If dynamic providers are re-introduced, they should be in their own app.
# SYNAPSE_NOTIFICATION_PROVIDERS = []

# This setting has been corrected to align with the actual URL names
# defined in each application's urls.py file.
SYNAPSE_MODULES = [
    {
        "app_name": "synapse_attendance",
        "display_name": "Attendance Analyzer",
        # CORRECTED: Was 'upload', changed to 'analyze' to match urls.py
        "url_name": "synapse_attendance:analyze",
        "description": "Analyze employee punch card data.",
        "placement": "toolbox",
        "order": 10,
    },
    {
        "app_name": "synapse_bom_analyzer",
        "display_name": "BOM Analyzer",
        # CORRECTED: Changed to 'analyze' to match urls.py
        "url_name": "synapse_bom_analyzer:analyze",
        "description": "Aggregate materials from multiple BOM files.",
        "placement": "toolbox",
        "order": 20,
    },
]

# NOTE: The complex LOGGING dictionary is a good candidate for simplification
# or can be kept as is if detailed logging is required. For a clean start,
# Django's default logging is often sufficient. We will keep yours for now.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
