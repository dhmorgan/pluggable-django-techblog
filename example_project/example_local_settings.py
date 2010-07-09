# -*- coding: utf-8 -*-

from django.conf import settings

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SERVE_MEDIA = False

ADMINS = [
    # (""),
]

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3", # Add "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
        "NAME": "dev.db",                       # Or path to database file if using sqlite3.
        "USER": "",                             # Not used with sqlite3.
        "PASSWORD": "",                         # Not used with sqlite3.
        "HOST": "",                             # Set to empty string for localhost. Not used with sqlite3.
        "PORT": "",                             # Set to empty string for default. Not used with sqlite3.
    }
}

TIME_ZONE = "US/Central"

USE_I18N = False

STATICFILES_DIRS = settings.STATICFILES_DIRS + []

SECRET_KEY = "nmhttt_4geb*9pizzapizzapizzab_tn3v85$$^0k4%="

AUTH_PROFILE_MODULE = "basic_profiles.Profile"
NOTIFICATION_LANGUAGE_MODULE = "account.Account"

ACCOUNT_OPEN_SIGNUP = False
ACCOUNT_REQUIRED_EMAIL = False
ACCOUNT_EMAIL_VERIFICATION = False
ACCOUNT_EMAIL_AUTHENTICATION = False
ACCOUNT_UNIQUE_EMAIL = EMAIL_CONFIRMATION_UNIQUE_EMAIL = False

EMAIL_CONFIRMATION_DAYS = 2
CONTACT_EMAIL = ""
SITE_NAME = ""

DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
}

