from django import template
from django.template.defaultfilters import stringfilter
import re
from django.template import Variable

def context_resolve(context, var, callable=None):
    resolved_var = Variable(var).resolve(context)
    if callable is not None:
        resolved_var = callable(resolved_var)
    return resolved_var


from techblog.apps.resources import models

register = template.Library()


def parse_dimensions(d):

    def to_int(s):
        try:
            return int(s)
        except ValueError:
            return None

    values = map(to_int, d.split()[:2])

    if not values:
        return None, None

    if len(values) == 1:
        return values[0], None

    return values

@register.simple_tag
def siteimage_width(name, dimensions):

    try:
        img_upload = models.ImageUpload.objects.get(name__iexact=name)
    except models.ImageUpload.DoesNotExist:
        raise template.TemplateSyntaxError("Unknown image (%s)" % str(name))

    width, height = parse_dimensions(dimensions)
    url, (w, h) = img_upload.thumb(width, height)

    return str(w or '')

@register.simple_tag
def siteimage_height(name, dimensions):

    try:
        img_upload = models.ImageUpload.objects.get(name__iexact=name)
    except models.ImageUpload.DoesNotExist:
        raise template.TemplateSyntaxError("Unknown image (%s)" % str(name))

    width, height = parse_dimensions(dimensions)
    url, (w, h) = img_upload.thumb(width, height)

    return str(h or '')


@register.simple_tag
def siteimage_url(name, dimensions):

    width, height = parse_dimensions(dimensions)

    try:
        img_upload = models.ImageUpload.objects.get(name__iexact=name)
    except models.ImageUpload.DoesNotExist:
        raise template.TemplateSyntaxError("Unknown image (%s)" % str(name))

    if width is not None:
        try:
            width = int(width)
        except ValueError:
            raise template.TemplateSyntaxError("Width must be a number")

    if height is not None:
        try:
            height = int(height)
        except ValueError:
            raise template.TemplateSyntaxError("Height must be a number")

    url = img_upload.image.url

    return url



@register.simple_tag
def siteimage(name, dimensions):

    width, height = parse_dimensions(dimensions)

    try:
        img_upload = models.ImageUpload.objects.get(name__iexact=name)
    except models.ImageUpload.DoesNotExist:
        raise template.TemplateSyntaxError("Unknown image (%s)" % str(name))

    if width is not None:
        try:
            width = int(width)
        except ValueError:
            raise template.TemplateSyntaxError("Width must be a number")

    if height is not None:
        try:
            height = int(height)
        except ValueError:
            raise template.TemplateSyntaxError("Height must be a number")

    url, (w, h) = img_upload.thumb(width, height)

    html = '<img src="%s" width="%s" height="%s" alt="%s" title="%s"></img>' % (url, w, h, img_upload.description, img_upload.description)

    return html


_re_siteimage_tag = re.compile(r'for (?P<object>\S+) as (?P<name>\S+) size (?P<size>\S+)')


class GetSiteimageNode(template.Node):
    def __init__(self, siteimage_name, value_name, size_name):
        self.siteimage_name = siteimage_name
        self.value_name = value_name
        self.size_name = size_name

    def render(self, context):

        width, height = parse_dimensions(context_resolve(context, self.size_name))

        name = context_resolve(context, self.siteimage_name)

        try:
            img_upload = models.ImageUpload.objects.get(name__iexact=name)
        except models.ImageUpload.DoesNotExist:
            raise template.TemplateSyntaxError("Unknown image (%s)" % str(name))

        url, (w, h) = img_upload.thumb(width, height)

        si = {}
        si['name'] = name
        si['url'] = url
        si['w'] = w
        si['h'] = h
        si['half_w'] = w/2
        si['half_h'] = h/2
        si['twice_w'] = w*2
        si['twice_h'] = h*2


        context[self.value_name] = si

        return ''


@register.tag
def get_siteimage(parser, token):

    directive = token.contents.strip().split(' ', 1)[1]

    match = _re_siteimage_tag.match(directive)

    if match is None:
        raise template.TemplateSyntaxError("Syntax error")

    siteimage_name = match.group(1)
    value_name = match.group(2)
    size_name = match.group(3)

    return GetSiteimageNode(siteimage_name, value_name, size_name)
