from django.conf import settings
_url_remap = settings.URL_REMAP

class UrlRemapMiddleware(object):

    """ Transparently maps one url on to another. """

    def process_request(self, request):
        request.path = unicode(_url_remap.get(request.path, request.path))
        request.path_info=request.path
