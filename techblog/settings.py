# Django settings for techblog2 project.
import os.path
from os.path import join
settings_path = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
     ('Will McGugan', 'will@willmcgugan.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = join(settings_path, 'techblog.db')             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = join(settings_path, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/adminmedia/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#qxry*06tp(w-s%1!#cutq9x-7c997imgz=b)2lkw@&!bef_k='

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (

    'django.middleware.cache.UpdateCacheMiddleware',



    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.middleware.cache.FetchFromCacheMiddleware',


    'techblog.middleware.UrlRemapMiddleware',

    #'debug_toolbar.middleware.DebugToolbarMiddleware',

)

ROOT_URLCONF = 'techblog.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    join(settings_path, 'templates'),
)



TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "techblog.context_processors.google_analytics"
    )


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

    'django.contrib.humanize',

    'django.contrib.admin',
    'django.contrib.sitemaps',

    'techblog.markup',

    'techblog.apps.blog',
    'techblog.apps.comments',
    'techblog.apps.pages',
    'techblog.apps.resources',
    #'debug_toolbar'
)

INTERNAL_IPS = ('127.0.0.1',)

CACHE_BACKEND = "memcached://127.0.0.1:11211/"
#CACHE_BACKEND = "dummy:///"

CACHE_MIDDLEWARE_ANONYMOUS_ONLY=True

#SESSION_ENGINE = "django.contrib.sessions.backends.cache"

DEFAULT_FROM_EMAIL = "will@willmcgugan.com"
SYSTEM_EMAIL_PREFIX = "[willmcgugan.com]"

DEFAULT_BLOG_SLUG = "rootblog"

ENABLE_COMMENTS = True

BLOG_POSTS_PER_PAGE = 10

if not DEBUG:
    PREPEND_WWW = True

#USE_ETAGS = True

# A dictionary that transparently maps one set of URLs on to another
# See techblog.middleware
URL_REMAP = {
    '/old/url/' : '/new/url'
}

# Path to your google analytics code
GA_PATH = ""



try:
    from local_settings import *
except ImportError:
    pass
