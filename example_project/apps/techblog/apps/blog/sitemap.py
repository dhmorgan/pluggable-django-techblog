from django.contrib.sitemaps import Sitemap
from django.conf import settings

from models import Post, Tag, Blog, Channel

from datetime import datetime, timedelta

class PostSitemap(Sitemap):

    def items(self):
        return Post.published_posts.all()

    def lastmod(self, obj):
        return max(obj.edit_time, obj.display_time)

    def changefreq(self, obj):

        now = datetime.now()
        t = obj.display_time
        days_since = (now - t).days

        if days_since < 1:
            return 'hourly'
        elif days_since < 7:
            return 'daily'
        elif days_since < 30:
            return 'weekly'
        elif days_since < 365:
            return 'monthly'
        else:
            return 'yearly'

    def priority(self, obj):
        return .9

    def location(self, obj):
        return obj.get_absolute_url()

class RootblogPostSitemap(PostSitemap):

    def items(self):
        try:
            blog = Channel.objects.get(slug=settings.DEFAULT_BLOG_SLUG)
        except Channel.DoesNotExist:
            try:
                blog = Blog.objects.get(slug=settings.DEFAULT_BLOG_SLUG)
            except Blog.DoesNotExist:
                blog = None
        if blog is None:
            return []
        return blog.posts()

    def location(self, obj):
        return '/' + obj.get_blog_relative_url()

    def priority(self, obj):
        return 1.0

class BlogSitemap(Sitemap):

    changefreq = 'daily'

    def items(self):
        blogs = Blog.objects.all()
        def get_page_count(blog):
            num_pages = 1 + (blog.posts().count() / settings.BLOG_POSTS_PER_PAGE)
            return num_pages
        index_pages = []
        for blog in blogs:
            index_pages += [(blog, page_no+1) for page_no in xrange(get_page_count(blog))]
        return index_pages

    def location(self, obj):
        blog, page_no = obj
        if page_no == 1:
            return blog.get_absolute_url()
        else:
            return "%spage/%i/" % (blog.get_absolute_url(), page_no)

    def priority(self, obj):
        return .5

    def lastmod(self, obj):
        blog, page_no = obj
        try:
            return blog.posts()[0].edit_time
        except IndexError:
            return blog.created_time


class ChannelSitemap(BlogSitemap):

    def items(self):
        blogs = Channel.objects.all()
        def get_page_count(blog):
            num_pages = 1 + (blog.posts().count() / settings.BLOG_POSTS_PER_PAGE)
            return num_pages
        index_pages = []
        for blog in blogs:
            index_pages += [(blog, page_no+1) for page_no in xrange(get_page_count(blog))]
        return index_pages

    def priority(self, obj):
        return .6

    def location(self, obj):
        blog, page_no = obj
        if page_no == 1:
            return blog.get_absolute_url()
        else:
            return "%spage/%i/" % (blog.get_absolute_url(), page_no)


class RootblogSitemap(BlogSitemap):

    priority = .7

    def items(self):
        try:
            blogs = [Channel.objects.get(slug=settings.DEFAULT_BLOG_SLUG)]
        except Channel.DoesNotExist:
            try:
                blogs = [Blog.objects.get(slug=settings.DEFAULT_BLOG_SLUG)]
            except Blog.DoesNotExist:
                blogs = []

        def get_page_count(blog):
            num_pages = 1 + (blog.posts().count() / settings.BLOG_POSTS_PER_PAGE)
            return num_pages
        index_pages = []
        for blog in blogs:
            index_pages += [(blog, page_no+1) for page_no in xrange(get_page_count(blog))]
        return index_pages

    def location(self, obj):
        blog, page_no = obj
        if page_no == 1:
            return "/"
        else:
            return "/page/%i/" % (page_no)



class TagSitemap(Sitemap):
    priority = 0.4

    def items(self):
        return Tag.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()
