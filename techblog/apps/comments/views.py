from models import Comment
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
from django.template.context import RequestContext
from django.core.cache import cache
import urlparse
from techblog.tools import clear_cached_page


from techblog import broadcast
from forms import CommentForm

import simplejson
import urllib

@broadcast.recieve()
def comment(**kwargs):

    try:
        comment = Comment.objects.get(email=kwargs.get('email'), created_time=kwargs.get('created_time'))
    except Comment.DoesNotExist:
        comment = Comment()
    for k, v, in kwargs.iteritems():
        setattr(comment, k, v)
    comment.save()
    if 'created_time' in kwargs:
        comment.created_time = kwargs['created_time']
    comment.save()

def escape(s):
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    return s

def xhr_post_comment(request, **kwargs):

    #if settings.DEBUG:
    #    import time
    #    time.sleep(3)

    errors = []

    form = CommentForm(request.POST)

    response = {'status': 'ok', 'errors' : []}
    if not form.is_valid():
        response['status'] = "fail"
        response['errors'] = dict((str(key), str(value)) for key, value in form.errors.iteritems())
    else:
        name = escape(form.cleaned_data.get('name', ''))
        email = form.cleaned_data.get('email', '')
        url = escape(form.cleaned_data.get('url', ''))
        if 'javascript' in url.lower():
            url = url.split(':', 1)[-1]
        if url.strip() and ':' not in url:
            url = 'http://' + url
        content = form.cleaned_data.get('content', '')
        content_format = form.cleaned_data.get('content_format', '')

        content_type = form.cleaned_data.get('content_type')
        object_id = int(form.cleaned_data.get('object_id'))

        success_url = form.cleaned_data.get('success_url')

        app_label, model = content_type.split('.')

        ct = ContentType.objects.get(app_label=app_label, model=model)
        object = ct.get_object_for_this_type(id=object_id)

        if not broadcast.safe_first.allow_comment(object):

            response['status'] = "fail"
            response['errors'].append('Commenting not permited on this object')

        else:

            comment = Comment(
                content_type = ct,
                content_object = object,
                name = name,
                email = email,
                url = url
            )
            comment.content_markup_type = 'comment_bbcode'
            comment.content = content

            broadcast.safe_call.new_comment(object, comment)

            comment.save()
            response['comment_id'] = comment.id
            response['fwd'] = '%s?%s#comment%d' % (reverse('post_success'), urllib.urlencode(dict(fwd = success_url)), comment.id)



    json = simplejson.dumps(response)
    return HttpResponse(json, mimetype='application/json')


def xhr_delete_comment(request, **kwargs):

    if request.user.is_anonymous():
        raise Http404

    result = ""

    comment_id = request.GET.get('comment_id', None)

    if comment_id is None:
        result = "fail"
    else:
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.delete()
            result = "success"
        except Comment.DoesNotExist:
            result = "fail"

    try:
        clear_cached_page(request.GET.get('url'))
    except:
        pass

    response = dict(result=result)
    json = simplejson.dumps(response)
    return HttpResponse(json, mimetype='application/json')


def post_success(request):

    url = request.GET.get('fwd', '/')


    return HttpResponseRedirect(url)