# Create your views here.
import models
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404, HttpResponseRedirect
from django.core.paginator import Paginator
from django.conf import settings
from django.template.context import RequestContext
import urllib
from django.db.models import Q
from django.contrib.auth.decorators import *

from datetime import datetime, timedelta
import tools
from techblog import broadcast
from techblog.markup import extendedmarkup
from django.template.defaultfilters import slugify
from django.views.decorators.cache import never_cache
from django.contrib.sites.models import Site
import urlparse
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from techblog.tools import clear_cached_page

import operator
from itertools import groupby
import forms

from techblog import mailer


# This is a sentinal date to overcome a subtle design flaw in the model
# It is slightly less painful that a DB migration
# New posts are given this date when first created, and the actual date is
# set when the post is published
DUMMY_DATE = datetime(1970, 1, 1)

def invalidate_cache(post):

    clear_cached_page(post.get_absolute_url())
    clear_cached_page('/'+post.get_blog_relative_url())
    clear_cached_page('/')
    clear_cached_page(post.blog.get_absolute_url())


@broadcast.recieve()
def allow_comment(object):
    if settings.ENABLE_COMMENTS and isinstance(object, models.Post):
        return True
    return False

@broadcast.recieve()
def new_comment(object, comment):
    if isinstance(object, models.Post):
        comment.moderated = True
        comment.visible = True
        comment.group = "blog.%s" % object.blog.slug
        comment.save()

        domain = Site.objects.get_current().domain
        td = {}
        td['name'] = object.blog.owner.get_full_name()
        td['comment'] = comment.content_text
        td['post'] = object.title
        td['url'] = "http://%s%s#comment%s" % (domain, object.get_absolute_url(), comment.id)

        invalidate_cache(object)

        mailer.send("admin/mail/newcomment.txt", td, "New Comment", object.blog.owner.email)
    else:
        raise broadcast.RejectBroadcast


def get_channel_or_blog(slug):
    if not slug:
        slug = settings.DEFAULT_BLOG_SLUG
    try:
        return models.Channel.objects.get(slug=slug)
    except models.Channel.DoesNotExist:
        return get_object_or_404(models.Blog, slug=slug)


def get_blog_list_data(request, posts, get_page_url, page_no):


    paginator = Paginator(posts, settings.BLOG_POSTS_PER_PAGE)

    if page_no > paginator.num_pages:
        raise Http404

    page = paginator.page(page_no)
    posts = page.object_list

    num_pages = paginator.num_pages

    newer_page_url = get_page_url(page_no - 1, num_pages)
    older_page_url = get_page_url(page_no + 1, num_pages)


    td = dict(page = page,
              page_no = page_no,
              posts = posts,
              older_page_url = older_page_url,
              newer_page_url = newer_page_url)

    return td


@cache_page(60*10)
def feeds(request, blog_slug, feed_item, **kwargs):

    from django.contrib.syndication.views import feed

    if '/' in feed_item:
        feed_type, slug = feed_item.split('/', 1)
    else:
        feed_type = feed_item
        slug =""

    if 'blog_root' in kwargs:
        del kwargs['blog_root']

    if feed_type == "posts":
        return feed(request, url="posts/%s"% ( blog_slug ), **kwargs)
    elif feed_type == "tag":
        return feed(request, url="tag/%s/%s"% ( blog_slug, feed_item ), **kwargs)
    raise Http404



@cache_page(60*60*12)
def blog_month(request, blog_slug, year, month, page_no=1, blog_root=None):

    page_no = int(page_no)

    year = int(year)
    month = int(month)

    blog = get_channel_or_blog(blog_slug)
    blog_root = blog_root or blog.get_absolute_url()

    try:
        start_date = datetime(year, month, 1)
        year_end = year
        next_month = month + 1
        if next_month == 13:
            next_month = 1
            year_end += 1
        end_date = datetime(year_end, next_month, 1)
    except ValueError:
        raise Http404

    title = blog.title


    posts = blog.posts().filter(display_time__gte=start_date, display_time__lt=end_date).select_related()

    if not posts.count():
        raise Http404

    archives = tools.collate_archives(blog, blog_root)

    def get_page_url(page_no, num_pages):
        if page_no < 1 or page_no > num_pages:
            return ""
        if page_no == 1:
            return "%s%i/%i/"%(blog_root, year, month)
            #return reverse("blog_month", kwargs = dict(blog_slug=blog_slug, year=year, month=month, blog_root=blog_root))
        else:
            return "%s%i/%i/page/%i/"%(blog_root, year, month, page_no)


    td = get_blog_list_data(request, posts, get_page_url, page_no)

    sections = blog.description_data.get('sections', None)

    td.update(  dict( blog_root = blog_root,
                blog = blog,
                sections = sections,
                title = title,
                page_title = title,
                tagline = blog.tagline,
                archives = archives,
                archive_month = month,
                archive_year = year) )

    sections = extendedmarkup.process(sections, td)

    return render_to_response(blog.get_template_names("month.html"),
                              td,
                              context_instance=RequestContext(request))



def blog_front(request, blog_slug="", page_no=1, blog_root=None):

    s = request.GET.get('s')
    if s:
        return HttpResponseRedirect(reverse('blog_search', kwargs=dict(blog_slug=blog_slug))+'?s='+s)

    page_no = int(page_no)
    if page_no < 1:
        raise Http404

    blog = get_channel_or_blog(blog_slug)
    blog_root = blog_root or blog.get_absolute_url()

    title = blog.title
    posts = blog.posts().select_related()


    #archives = tools.collate_archives(blog)

    def get_page_url(page_no, num_pages):
        if page_no < 1 or page_no > num_pages:
            return ""
        if page_no == 1:
            return blog_root
        else:
            return "%spage/%i/" % (blog_root, page_no)

    td = get_blog_list_data(request, posts, get_page_url, page_no)

    sections = blog.description_data.get('sections', None)

    feeds = [blog.get_feed()]

    td.update(  dict(   blog_root = blog_root,
                        blog = blog,
                        title = title,
                        page_title = title,
                        tagline = blog.tagline,
                        #archives = archives,
                        sections = sections,
                        feeds = feeds) )

    sections = extendedmarkup.process(sections, td)

    return render_to_response(blog.get_template_names("index.html"),
                              td,
                              context_instance=RequestContext(request))


    #return posts


@cache_page(60*60)
def blog_post(request, blog_slug, year, month, day, slug, blog_root=None):

    blog = get_channel_or_blog(slug=blog_slug)
    blog_root = blog_root or blog.get_absolute_url()

    year = int(year)
    month = int(month)
    day = int(day)

    post_day_start = datetime(year, month, day)
    post_day_end = post_day_start + timedelta(days=1)

    if post_day_start > datetime.now():
        raise Http404

    if request.user.is_anonymous():
        post = get_object_or_404(models.Post,
                                 display_time__gte=post_day_start,
                                 display_time__lt=post_day_end,
                                 slug=slug,
                                 version='live',
                                 published=True)
    else:
        post = get_object_or_404(models.Post,
                                 display_time__gte=post_day_start,
                                 display_time__lt=post_day_end,
                                 slug=slug,
                                 version='live',
                                 version_id=None)


    is_preview = False
    if 'version' in request.GET and not request.user.is_anonymous():
        version = request.GET.get('version')
        if not post.version_exists(version):
            raise Http404
        post = post.get_version(version)
        is_preview = True

    if not request.user.is_anonymous() and request.GET.has_key('clearcache'):
        invalidate_cache(post)


    sections = extendedmarkup.combine_sections( blog.description_data.get('sections', None),
                                 post.content_data.get('sections', None) )


    prev_post = None
    next_post = None
    try:
        prev_post = blog.posts().filter(published=True, display_time__lt=post.display_time).order_by('-display_time')[0]
    except IndexError:
        pass

    try:
        next_post = blog.posts().filter(published=True, display_time__gt=post.display_time).order_by('display_time')[0]
    except IndexError:
        pass

    tags = list(post.tags.all().order_by('slug'))
    #tags.sort(key = lambda t:t.name.lower())


    td = dict(  blog_root = blog_root,
                blog=blog,
                year=year,
                month=month,
                day=day,
                post=post,
                prev_post=prev_post,
                next_post=next_post,
                page_title = post.title,
                tagline = post.blog.title,
                tags = tags,
                sections = sections,
                user = request.user,
                is_preview = is_preview )

    sections = extendedmarkup.process(sections, td)

    return render_to_response(blog.get_template_names("entry.html", [post.template_path]),
                              td,
                              context_instance=RequestContext(request))


def tag(request, blog_slug, tag_slug, page_no=1, blog_root=None):

    page_no = int(page_no)
    if page_no < 1:
        raise Http404

    blog = get_channel_or_blog(blog_slug)
    blog_root = blog_root or blog.get_absolute_url()

    try:
        tag = blog.get_tag(tag_slug)
    except models.Tag.DoesNotExist:
        raise Http404

    title = blog.title
    posts = tag.posts()


    paginator = Paginator(posts, 10)

    if page_no > paginator.num_pages:
        raise Http404

    page = paginator.page(page_no)
    posts = page.object_list

    def get_page_url(page_no):
        if page_no < 1 or page_no > paginator.num_pages:
            return ""
        if page_no == 1:
            return "%stag/%s/"%(blog_root, tag_slug)
        else:
            return "%stag/%s/page/%i/" % (blog_root, tag_slug, page_no)


    newer_page_url = get_page_url(page_no - 1)
    older_page_url = get_page_url(page_no + 1)

    sections = extendedmarkup.combine_sections( blog.description_data.get('sections', None),
                                 tag.description_data.get('sections', None) )


    feeds = [tag.get_feed()]

    td = dict(blog_root = blog_root,
              blog = blog,
              tag = tag,
              title = title,
              page_title = title,
              tagline = blog.tagline,
              #archives = archives,
              page = page,
              page_no = page_no,
              posts = posts,
              sections = sections,
              older_page_url = older_page_url,
              newer_page_url = newer_page_url,
              feeds = feeds)


    sections = extendedmarkup.process(sections, td)

    return render_to_response(blog.get_template_names("tag.html"),
                              td,
                              context_instance=RequestContext(request))

from techblog.markup.render import render_comment

def xhr_preview_comment(request, **kwargs):

    bbcode = request.REQUEST.get('bbcode', '')
    html, summary, text, data = render_comment(bbcode, 'comment_bbcode')

    comment = {}
    comment['content_html'] = html
    comment['url'] = request.REQUEST.get('url')
    comment['name'] = request.REQUEST.get('name')
    comment['email'] = request.REQUEST.get('email')
    comment['created_time'] = datetime.now()

    td = {}
    td['comment'] = comment

    return render_to_response("xhr_comment_preview.html",
                              td,
                              context_instance=RequestContext(request))


@login_required
def import_wxr(request, blog_slug='', blog_root=''):

    from forms import ImportForm

    if request.method == "POST":

        form = ImportForm(request.POST, request.FILES)

        if form.is_valid():

            if form.cleaned_data.get('format') == "WXR":

                blog_slug = form.cleaned_data['blog_slug']
                included_tags = form.cleaned_data['include_tags']
                excluded_tags = form.cleaned_data['exclude_tags']
                wxr_file = request.FILES['input_file']
                tools.import_wxr(blog_slug, wxr_file, included_tags, excluded_tags)
    else:

        form = ImportForm()

    td = dict(form=form)


    return render_to_response("blog/tools/import_wxr.html",
                              td,
                              context_instance=RequestContext(request))

def blog_search(request, blog_slug, blog_root=None):

    MAX_RESULTS = 100

    s = request.GET.get('s', '').strip()

    blog = get_channel_or_blog(blog_slug)
    blog_root = blog_root or blog.get_absolute_url()

    if isinstance(blog, models.Channel):
        blogs = list(blog.blogs.all())
    else:
        blogs = [blog]

    sections = blog.description_data.get('sections', None)
    #sections = extendedmarkup.combine_sections( blog.description_data.get('sections', None), sections)

    from string import punctuation
    normalized_s = "".join(c for c in s if c not in punctuation)

    if normalized_s:
        query = Q(title__icontains=normalized_s) | Q(content_text__icontains=normalized_s)
        posts = models.Post.published_posts.filter(blog__in=blogs, version="live").filter(query).distinct().order_by("-display_time")[:MAX_RESULTS]
        num_results = posts.count()
    else:
        posts = []
        num_results = 0

    query_words=normalized_s.split()
    if query_words:
        tag_query = reduce(operator.or_, [Q(name__icontains=word) for word in query_words])
        tags = models.Tag.objects.filter(blog__in=blogs).filter(tag_query).distinct()
    else:
        tags = []

    tags = [itags.next() for (tag_name, itags) in groupby(tags, lambda t:t.slug)]

    td = dict(blog_root = blog_root,
              blog=blog,
              sections=sections,
              posts=posts,
              tags=tags,
              num_results=num_results,
              search_term=s)

    return render_to_response(blog.get_template_names("search.html"),
                              td,
                              context_instance=RequestContext(request))

def front(request, blog_root=None):
    template_data = {}
    return render_to_response("blog_base.html",
                              template_data,
                              context_instance=RequestContext(request))

@login_required
def newpost(request, blog_slug, blog_root=None):

    blog = get_object_or_404(models.Blog, slug=blog_slug)
    default_slug = slugify(str(datetime.now()))

    post = models.Post( blog=blog,
                        title="Post",
                        slug=default_slug,
                        published=False,
                        created_time=datetime.now(),
                        edit_time=datetime.now(),
                        display_time=DUMMY_DATE,
                        content='',
                        content_markup_type="emarkup",
                        version='live')
    post.save()

    return HttpResponseRedirect(reverse(writer, args=(blog_slug, post.id)))

@login_required
def writer(request, blog_slug, post_id, blog_root=None):

    blog = get_channel_or_blog(blog_slug)
    blog_root = blog_root or blog.get_absolute_url()
    post = get_object_or_404(models.Post, id=int(post_id), version='live')


    edit_post = post

    if post.version_exists('draft'):
        draft_post = post.get_version('draft')
        post = draft_post


    post_slug = post.slug
    if '|' in post_slug:
        post_slug = post_slug.split('|', 1)[-1]

    auto_url = ''

    def save_to(save_post):
        save_post.title = request.POST.get('title', save_post.title)

        save_post.slug = request.POST.get('slug', save_post.slug)

        if not save_post.slug.strip():
            save_post.slug = slugify(save_post.title)

        save_post.tags_text = request.POST.get('tags_text', save_post.tags_text)
        save_post.content = request.POST.get('content', save_post.content)
        save_post.published = request.POST.get('published', save_post.published) == 'on'
        save_post.allow_comments = request.POST.get('allow_comments', save_post.allow_comments) == 'on'
        save_post.save()


    if request.method == "POST":

        if 'save' in request.POST:

            draft_post = edit_post.get_version('draft')
            save_to(draft_post)
            post = draft_post
            edit_post.delete_version('preview')

        elif 'revert' in request.POST:

            edit_post.delete_version('draft')
            edit_post.delete_version('preview')
            post = edit_post
            #draft_post = edit_post.get_version('draft')
            #post = draft_post

        elif 'publish' in request.POST:

            save_to(edit_post)
            if edit_post.display_time == DUMMY_DATE:
                edit_post.display_time = datetime.now()
            post_url = reverse('blog_post', args=(blog.slug, edit_post.display_time.year, edit_post.display_time.month, edit_post.display_time.day, edit_post.slug))
            edit_post.delete_version('preview')
            edit_post.delete_version('draft')
            post = edit_post
            post.published = True
            post.save()
            return HttpResponseRedirect(post_url)

        elif 'preview' in request.POST:

            preview_post = edit_post.get_version('preview')
            save_to(preview_post)
            post_url = reverse('blog_post', args=(blog.slug, edit_post.display_time.year, edit_post.display_time.month, edit_post.display_time.day, edit_post.slug))
            auto_url = post_url + "?version=preview"
            post = preview_post

        form = forms.WriterForm()

    else:
        form = forms.WriterForm()


    td = dict( blog_root = blog_root,
               post_slug=post_slug,
               blog=blog,
               post=post,
               edit_post=edit_post,
               form=form,
               auto_url=auto_url
               )

    return render_to_response("blog/write.html",
                              td,
                              context_instance=RequestContext(request))

@login_required
def manage(request, blog_root="", blog_slug=""):

    td = {}

    blogs = models.Blog.objects.all().order_by('title')
    channels = models.Channel.objects.all().order_by('title')

    td['sections'] = ''
    td['blogs'] = blogs
    td['channels'] = channels

    drafts = models.Post.objects.filter(version='draft', published=False).order_by('id')
    td['drafts'] = drafts

    if settings.CACHE_BACKEND.startswith('memcache'):
        import memcache
        c = memcache.Client([settings.CACHE_BACKEND.split(':',1)[1].strip('/')])
        cache_stats = c.get_stats()[0][1]
        td['cache_stats'] = cache_stats.items()

    return render_to_response("blog/manage.html",
                              td,
                              context_instance=RequestContext(request))