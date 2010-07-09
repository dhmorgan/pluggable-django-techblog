from django.conf import settings

for app in settings.INSTALLED_APPS:
    try:
        __import__(app+".views")
    except ImportError:
        pass