import models
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404
from django.contrib.auth.decorators import *
from django.template.context import RequestContext
from django.core.urlresolvers import reverse

from techblog import broadcast
import forms

from django.conf import settings
from django.template.defaultfilters import slugify
from django.contrib.sites.models import Site

from techblog import mailer

@broadcast.recieve()
def allow_comment(object):
    if isinstance(object, models.Page):
        return True
    return False

@broadcast.recieve()
def new_comment(object, comment):
    if isinstance(object, models.Page):
        comment.moderated = True
        comment.visible = True
        page = object

        domain = Site.objects.get_current().domain
        for name, email in settings.ADMINS:
            td = {}
            td['name'] = name
            td['comment'] = comment.content_text
            td['post'] = page.title
            td['url'] = "http://%s%s" % (domain, object.get_absolute_url())
            mailer.send("admin/mail/newcomment.txt", td, "New Comment", email)

    else:
        raise broadcast.RejectBroadcast




def page(request, path):

    path = path.rstrip('/')
    page = get_object_or_404(models.Page, path=path, version='live')

    if request.user.is_anonymous() and not page.published:
        raise Http404

    is_preview = False
    if 'version' in request.GET and not request.user.is_anonymous():
        version = request.GET.get('version')
        if not page.version_exists(version):
            raise Http404
        page = page.get_version(version)
        is_preview = True

    sections = page.get_sections()


    preview_comment_url = reverse('xhr_preview_comment', args=[settings.DEFAULT_BLOG_SLUG])

    td = dict( page=page,
               sections=sections,
               is_preview=is_preview,
               user = request.user,
               preview_comment_url = preview_comment_url)

    return render_to_response(page.get_template_names(),
                              td,
                              context_instance=RequestContext(request))


@login_required
def newpage(rquest):

    page_count = models.Page.objects.all().count()
    page = models.Page( title="New Page",
                        slug="new-page-%i"%page_count,
                        inherit=False,
                        published=False,
                        promoted=False,
                        version="live" )

    page.save()
    return HttpResponseRedirect(reverse(writer, args=(page.id,)))

@login_required
def writer(request, page_id):

    page = get_object_or_404(models.Page, id=page_id, version='live')

    edit_page = page

    if page.version_exists('draft'):
        draft_page = page.get_version('draft')
        page = draft_page

    page_slug = page.slug
    if '|' in page_slug:
        page_slug = page_slug.split('|', 1)[-1]

    auto_url = ''

    def save_to(save_page):
        a=request.POST.get

        save_page.title = a('title', save_page.title)
        save_page.slug = a('slug', save_page.slug)
        if not save_page.slug.strip():
            save_page.slug = slugify(save_page.title)
        save_page.inherit = a('inherit', save_page.inherit) == 'on'
        save_page.promoted = a('promoted', save_page.promoted) == 'on'
        save_page.published = a('published', save_page.published) == 'on'
        save_page.allow_comments = a('allow_comments', save_page.published) == 'on'
        save_page.content = a('content', save_page.content)
        save_page.content_markup_type="emarkup"
        save_page.save()

    if request.method == "POST":

        if 'save' in request.POST:

            draft_page = edit_page.get_version('draft')
            save_to(draft_page)
            page = draft_page
            edit_page.delete_version('preview')

        elif 'revert' in request.POST:

            edit_page.delete_version('draft')
            edit_page.delete_version('preview')
            page = edit_page
            #draft_page = edit_page.get_version('draft')
            #page = draft_page

        elif 'publish' in request.POST:

            save_to(edit_page)
            page_url = reverse('page', args=(edit_page.path,))
            edit_page.delete_version('preview')
            edit_page.delete_version('draft')
            page = edit_page
            page.published = True
            page.save()
            return HttpResponseRedirect(page_url)

        elif 'preview' in request.POST:

            preview_page = edit_page.get_version('preview')
            save_to(preview_page)
            page_url = reverse('page', args=(edit_page.path,))
            auto_url = page_url + "?version=preview"
            page = preview_page

        form = forms.WriterForm()

    else:

        form = forms.WriterForm()

    td = dict(  page_slug=page_slug,
                page=page,
                auto_url=auto_url,
                edit_page=edit_page,
                form=form)

    return render_to_response("page/write.html",
                              td,
                              context_instance=RequestContext(request))