from django import template
from django.template.defaultfilters import stringfilter
import re
from techblog.apps.blog import tools, models
from techblog.apps.comments.models import Comment
from django.template import Variable

register = template.Library()
import postmarkup


from django.template.loader import get_template, select_template
from django.template.context import Context
from django.template.defaultfilters import urlize


short_months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
long_months = "January February March April May June July August September October November December".split()


@register.filter
@stringfilter
def textilize(value):
    return postmarkup.textilize(value)


def context_resolve(context, var, callable=None):
    resolved_var = Variable(var).resolve(context)
    if callable is not None:
        resolved_var = callable(resolved_var)
    return resolved_var


_hash_tags = re.compile(r'(?:^|\s)\#(\w+)')
#_hash_tags_urls = re.compile(r'(http:\S+)|(?:^|\s)\#(\w+)')
_hash_tags_urls = re.compile(r'\s(http[:/\.\w-]+)|#(\w+)')

_microblog_user = re.compile(r'(^|\s)\@\w+')

def urlize_hashtags(txt, blog_root, post):

    tags = dict((t.name.lower(),t) for t in post.get_tags())

    def repl_hash(match):

        url, tag_name = match.group(1), match.group(2)
        if url:
            return ' <a href="%s">%s</a>' % (url, url)
        else:
            tag = tags.get(tag_name.lower())
            if tag is None:
                return " #"+tag_name
            link = blog_root + tag.get_blog_relative_url()
            return ' #<a href="%s">%s</a>' % (link, tag_name)

    return _hash_tags_urls.sub(repl_hash, txt).lstrip()


@register.simple_tag
def microblog(post, blog_root):
    content = urlize_hashtags(post.content_html, blog_root, post)
    #content = urlize(content)
    return content


@register.filter
@stringfilter
def shortmonth(value):
    try:
        month_index = int(value)
    except ValueError:
        return "INVALID MONTH"

    return short_months[month_index-1]


@register.filter
@stringfilter
def longmonth(value):
    try:
        month_index = int(value)
    except ValueError:
        return "INVALID MONTH"

    return long_months[month_index-1]

_re_first_paragraph = re.compile(r"<p>.*?</p>")

@register.filter
@stringfilter
def first_paragraph(value):
    match = _re_first_paragraph.match(value)
    if not match:
        return value
    return match.group(0)


@register.filter
@stringfilter
def smart_title(value):
    def title(word):
        for c in word:
            if c.isupper():
                return word
        return word.title()
    return u" ".join(title(value) for value in value.split())


@register.simple_tag
def get_post_url(blog_root, post=None):
    if post is None:
        return blog_root
    url = blog_root + post.get_blog_relative_url();
    return url


_re_archives_tag = re.compile(r'for (?P<object>\w+) as (?P<name>\w+)')

class GetArchivesNode(template.Node):
    def __init__(self, blog_name, value_name):
        self.blog_name = blog_name
        self.value_name = value_name

    def render(self, context):

        blog = context.get(self.blog_name, None)
        if object is None:
            return ''

        archives = tools.collate_archives(blog, context.get('blog_root'))

        context[self.value_name] = archives
        return ''

@register.tag
def get_archives(parser, token):

    directive = token.contents.strip().split(' ', 1)[1]

    match = _re_archives_tag.match(directive)

    if match is None:
        raise template.TemplateSyntaxError("Syntax error")

    blog_name = match.group(1)
    value_name = match.group(2)

    return GetArchivesNode(blog_name, value_name)


_re_tags_tag = re.compile(r'for (?P<object>\w+) as (?P<name>\w+) max (?P<count>\S+)')


class GetTagsNode(template.Node):
    def __init__(self, blog_name, value_name, max_count):
        self.blog_name = blog_name
        self.value_name = value_name
        self.max_count = max_count

    def render(self, context):

        try:
            blog = context.get(self.blog_name, None)
            if blog is None:
                return ''

            tags = blog.get_tag_cloud(context_resolve(context, self.max_count, int))

            context[self.value_name] = tags
            return ''
        except Exception, e:
            raise


@register.tag
def get_tags(parser, token):

    try:

        directive = token.contents.strip().split(' ', 1)[1]
        match = _re_tags_tag.match(directive)

        if match is None:
            raise template.TemplateSyntaxError("Syntax error")

        blog_name = match.group(1)
        value_name = match.group(2)

        max_count = match.group(3)

        return GetTagsNode(blog_name, value_name, max_count)
    except Exception, e:
        pass


class GetRecentNode(template.Node):
    def __init__(self, blog_name, value_name, max_count):
        self.blog_name = blog_name
        self.value_name = value_name
        self.max_count = max_count

    def render(self, context):

        blog = context.get(self.blog_name, None)
        if object is None:
            return ''

        posts = blog.posts()[:context_resolve(context, self.max_count, int)]

        context[self.value_name] = posts
        return ''


@register.tag
def get_recent_posts(parser, token):

    directive = token.contents.strip().split(' ', 1)[1]
    match = _re_tags_tag.match(directive)

    if match is None:
        raise template.TemplateSyntaxError("Syntax error")

    blog_name = match.group(1)
    value_name = match.group(2)
    max_count = match.group(3)


    return GetRecentNode(blog_name, value_name, max_count)



class GetRecentCommentsNode(template.Node):
    def __init__(self, blog_name, value_name, max_count):
        self.blog_name = blog_name
        self.value_name = value_name
        self.max_count = max_count

    def render(self, context):

        blog = context.get(self.blog_name, None)
        if object is None:
            return ''

        if isinstance(blog, models.Channel):
            blogs = list(blog.blogs.all())
        else:
            blogs = [blog]

        max_count = context_resolve(context, self.max_count, int)

        groups = ["blog." + b.slug for b in blogs]
        comments = Comment.objects.filter_for_model(models.Post).filter(group__in=groups).order_by('-created_time')[:max_count]

        context[self.value_name] = comments

        return ''


@register.tag
def get_recent_comments(parser, token):

    directive = token.contents.strip().split(' ', 1)[1]

    match = _re_tags_tag.match(directive)

    if match is None:
        raise template.TemplateSyntaxError("Syntax error")

    blog_name = match.group(1)
    value_name = match.group(2)
    max_count = match.group(3)

    return GetRecentCommentsNode(blog_name, value_name, max_count)


_re_related_posts_tag = re.compile(r'for (?P<object>\w+) as (?P<name>\w+) max (?P<count>\S+)')


class GetRelatedPostsNode(template.Node):
    def __init__(self, post_name, value_name, max_count):
        self.post_name = post_name
        self.value_name = value_name
        self.max_count = max_count

    def render(self, context):

        post = context.get(self.post_name, None)
        if object is None:
            return ''

        max_count = context_resolve(context, self.max_count, int)

        related_posts = post.get_related_posts(max_count)

        context[self.value_name] = related_posts

        return ''


@register.tag
def get_related_posts(parser, token):

    directive = token.contents.strip().split(' ', 1)[1]

    match = _re_tags_tag.match(directive)

    if match is None:
        raise template.TemplateSyntaxError("Syntax error")

    post_name = match.group(1)
    value_name = match.group(2)
    max_count = match.group(3)

    return GetRelatedPostsNode(post_name, value_name, max_count)




class RenderPostNode(template.Node):
    def __init__(self, post_name, template_fname):
        self.post_name = post_name
        self.template_fname = template_fname

    def render(self, context):

        post = context.get(self.post_name, None)
        if post is None:
            return ''

        templates = post.get_template_names(self.template_fname)

        template = select_template(templates)
        try:
            html = template.render(context)
        except Exception, e:
            error = str(e)
            error_template = select_template(['blog/modules/error.html'])
            html = unicode(error_template.render(Context(dict(error=error))))

        return html

@register.tag
def render_post(parser, token):
    post_name = token.contents.split()[1]
    return RenderPostNode(post_name, 'full.html')


@register.tag
def render_post_brief(parser, token):
    post_name = token.contents.split()[1]
    return RenderPostNode(post_name, 'brief.html')
