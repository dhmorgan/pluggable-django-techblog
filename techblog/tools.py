from django.core.cache import cache
import urlparse
from django.conf import settings

from django.utils.cache import md5_constructor, iri_to_uri

def generate_cache_key(key_prefix, path):
    """Returns a cache key for the header cache."""
    path = md5_constructor(iri_to_uri(path))
    return 'views.decorators.cache.cache_header.%s.%s' % (key_prefix, path.hexdigest())

def clear_cached_page(path):

    key_prefix = getattr(settings, 'CACHE_MIDDLEWARE_KEY_PREFIX', '')
    cache_key = generate_cache_key(key_prefix, path)
    cache.delete(cache_key)