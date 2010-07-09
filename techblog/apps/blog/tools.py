#!/usr/bin/env python
import models
from django.core.urlresolvers import reverse
from itertools import groupby
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import transaction

from techblog import broadcast
import time
import datetime
import re
#from BeautifulSoup import BeautifulSoup

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

def collate_archives(blog, blog_root):

    """Groups the posts for a blog by month.

    blog -- A Blog model

    Returns a list of tuples containing the year (as an integer),
    the month (integer) and the number of posts in that month (integer).

    """

    posts = blog.posts().values('display_time').order_by("-display_time")

    def count_iterable(i):
        return sum(1 for _ in i)

    def year_month(post):
        display_time = post['display_time']
        return (display_time.year, display_time.month)

    def month_details(year, month, post_group):
        url = "%s%i/%i/" % (blog_root, year, month)
        return url, year, month, count_iterable(post_group)

    months = [month_details(year, month, post_group) for (year, month),post_group in groupby(posts, year_month)]

    years = [(year,list(months)) for (year, months) in groupby(months, lambda m:m[1])]


    return years


@transaction.commit_on_success
def import_wxr(blog_slug, wxr_file, included_tags, excluded_tags):

    included_tags = set(t.strip().lower() for t in included_tags.split(',') if t)
    excluded_tags = set(t.strip().lower() for t in excluded_tags.split(',') if t)

    namespaces = """
        xmlns:excerpt="http://wordpress.org/export/1.0/excerpt/"
        xmlns:content="http://purl.org/rss/1.0/modules/content/"
        xmlns:wfw="http://wellformedweb.org/CommentAPI/"
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:wp="http://wordpress.org/export/1.0/"
"""

    content_ns = "http://purl.org/rss/1.0/modules/content/"
    wp_ns = "http://wordpress.org/export/1.0/"

    blog = models.Blog.objects.get(slug=blog_slug)

    wxr = ET.parse(wxr_file)

    items = wxr.findall(".//item")

    def get_text(item, name, ns=None, default=""):
        if ns is None:
            el = item.find(".//%s" % name)
        else:
            el = item.find(".//{%s}%s" % (ns, name))
        if el is not None:
            if el.text is None:
                return default
            return el.text
        return default

    pre_lang_re = re.compile(r'<pre lang="(\w+)">(.*?)<\/pre>', re.S)
    pre_re = re.compile(r'<pre>(.*?)<\/pre>', re.S)
    url_re = re.compile(r'http[s]*://\w*.\S*', re.S)

    def fix_html(html):

        html = html.replace("<h2>", "\n\n<h3>")
        html = html.replace("</h2>", "</h3>\n\n")
        html = html.replace('<p>', '\n\n')
        html = html.replace('</p>', '\n\n')
        html = html.replace('<pre', '\n\n<pre')
        html = html.replace('</pre>', '\n</pre>\n\n')

        lines = []
        lines.append("{..html}")

        p_start = None
        pre = False
        for line in html.split('\n'):
            #line = line.replace('\n', '<br/>')
            if "/pre>" in line:
                pre = False
                lines.append(line)
                continue
            if "<pre" in line:
                pre = True
            if pre:
                line = line.replace('&gt;', '>')
                line = line.replace('&lt;', '<')
                line = line.replace('&amp;', '&')
                lines.append(line)
                continue
            line = line.strip()
            if line:
                if not line.startswith('<'):
                    lines.append("\n<p>%s</p>"%line)
                else:
                    lines.append(line)

        html = "\n".join(lines)

        def repl_lang(match):
            return "\n\n{..code}\n{..language=%s}\n%s\n\n{..html}\n" % (match.group(1).lower(), match.group(2))
        html = pre_lang_re.sub(repl_lang, html)

        def repl(match):
            if '>>>' in match.group(1):
                language = 'pycon'
            else:
                language = 'python'
            return "\n\n{..code}\n{..language=%s}\n%s\n\n{..html}\n" % (language, match.group(1))
        html = pre_re.sub(repl, html)

        return html



    if items is not None:

        for item in items:

            post_type = get_text(item, "post_type", wp_ns)
            if post_type!="post":
                continue

            status = get_text(item, 'status')
            if status.lower() == "draft":
                continue

            guid = get_text(item, 'guid')
            title = get_text(item, 'title')

            if not title or not guid:
                continue
            slug = slugify(title)
            content = get_text(item, 'encoded', content_ns)

            pub_date = get_text(item, 'pubDate')
            pub_date = datetime.datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S +0000")
            #pub_date = datetime.datetime(*pub_date)


            catagories = set(category.text.lower() for category in item.findall(".//category"))
            tags = ",".join(catagories)

            if included_tags:
                if not included_tags.intersection(catagories):
                    continue
            elif excluded_tags:
                if excluded_tags.intersection(catagories):
                    continue

            #content = BeautifulSoup(content).prettify()
            #content = tidy.parseString(content)

            content = fix_html(content)


            try:
                new_post = models.Post.objects.get(guid=guid)
                continue
            except models.Post.DoesNotExist:
                new_post = models.Post()

            new_post_data = dict(   blog=blog,
                                    title=title,
                                    slug=slug,
                                    guid=guid,
                                    published=True,
                                    allow_comments=True,

                                    created_time=pub_date,
                                    edit_time=pub_date,
                                    display_time=pub_date,

                                    tags_text=tags,
                                    content=content,
                                    content_markup_type="emarkup")

            for k, v in new_post_data.iteritems():
                setattr(new_post, k, v)
            new_post.save()

            comments = item.findall(".//{%s}comment" % wp_ns)

            if comments is not None:
                for comment in comments:

                    if get_text(comment, "comment_approved", wp_ns) != "1":
                        continue

                    name = get_text(comment, "comment_author", wp_ns)
                    email = get_text(comment, "comment_author_email", wp_ns)
                    url = get_text(comment, "comment_author_url", wp_ns)
                    content = get_text(comment, "comment_content", wp_ns)
                    date = get_text(comment, "comment_date", wp_ns)

                    date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

                    ct = ContentType.objects.get_for_model(new_post)
                    ct_id = ".".join( (ct.app_label, ct.model) )

                    def repl_url(match):
                        url = match.group(0).strip()+" "
                        return '<a href="%s">%s</a>' % (url, url)
                    #content = url_re.sub(repl_url, content)
                    content.replace('<pre>\n', '<pre>')
                    content = content.replace('\n', '<br/>')
                    content = "<p>%s</p>" % content

                    broadcast.call.comment(object_id = new_post.id,
                                           visible=True,
                                           moderated=True,
                                           created_time=date,
                                           name = name,
                                           email=email,
                                           url=url,
                                           content=content,
                                           content_markup_type="html",
                                           content_type=ct,
                                           group="blog."+blog.slug)
