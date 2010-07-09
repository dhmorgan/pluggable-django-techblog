#!/usr/bin/env python
from models import Blog, Channel, Post, Tag
from django.contrib.syndication.feeds import Feed
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.contrib.syndication.feeds import FeedDoesNotExist
from django.shortcuts import get_object_or_404

MAX_ENTRIES = 20

def get_channel_or_blog(slug):
    try:
        return Channel.objects.get(slug=slug)
    except Channel.DoesNotExist:
        return get_object_or_404(Blog, slug=slug)

class BlogFeed(Feed):

    @classmethod
    def get_url(self, blog):
        return reverse('blog_feeds', args=[blog.slug, 'posts'])

    def get_object(self, bits):
        if len(bits) != 1:
            raise FeedDoesNotExist
        #blog = Blog.objects.get(slug=bits[0])
        blog = get_channel_or_blog(bits[0])
        return blog

    def items(self, blog):
        return blog.posts()[:MAX_ENTRIES]

    def title(self, blog):
        return blog.title

    def link(self, blog):
        if not blog:
            raise FeedDoesNotExist
        return blog.get_absolute_url()

    def description(self, blog):
        return mark_safe(blog.description_text)


    def item_pubdate(self, post):
        return post.display_time


class ChannelFeed(BlogFeed):

    def get_object(self, bits):
        if len(bits) != 1:
            raise FeedDoesNotExist
        channel = Channel.objects.get(slug=bits[0])
        return channel



class BlogTagFeed(Feed):

    @classmethod
    def get_url(self, tag):
        return reverse('blog_feeds', args=[tag.blog.slug, "tag/"+tag.slug])

    def get_object(self, bits):
        if len(bits) != 3:
            raise FeedDoesNotExist

        blog_slug = bits[0]
        tag_slug = bits[2]

        blog = get_channel_or_blog(blog_slug)

        tag = blog.get_tag(tag_slug)

        #tag = Tag.objects.get(blog__slug = blog_slug, slug=tag_slug)
        return tag

    def items(self, tag):
        return tag.posts()[:MAX_ENTRIES]

    def title(self, tag):
        return "%s posts in '%s'" % (tag.name.title(), tag.blog.title)

    def link(self, tag):
        if not tag:
            raise FeedDoesNotExist
        return tag.get_absolute_url()

    def description(self, tag):
        return mark_safe(tag.description_text)

    def item_pubdate(self, post):
        return post.display_time


class ChannelTagFeed(BlogTagFeed):

    #@classmethod
    #def get_url(self, tag):
    #    return reverse('blog_feeds', kwargs={'blog_slug':blog.slug, 'url':'blog'})

    @classmethod
    def get_url(self, tag):
        return reverse('blog_feeds', args=[tag.blog.slug, "tag/"+tag.slug])

    def get_object(self, bits):
        if len(bits) != 2:
            raise FeedDoesNotExist

        channel = Channel.objects.get(slug=bits[0])

        blog_slug = bits[0]
        tag_slug = bits[1]

        tag = channel.get_channel_tag(tag_slug)
        return tag
