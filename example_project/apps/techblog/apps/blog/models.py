from django.db import models

from django.contrib.auth.models import User
from techblog.markup.fields import PickledObjectField
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

from django.contrib.auth.models import User

from techblog.markup.render import render
from techblog.markup.fields import MarkupField
from techblog import broadcast

import markup
import operator
import datetime
import os
import os.path
from itertools import groupby

from django.contrib.sitemaps import ping_google

@broadcast.recieve
def new_content_on_site():
    ping_google('/sitemap.xml')




#
#from django.db.models.signals import post_save
#
#
#def _process_tags_signal(sender, **kwargs):
#    sender.
#
#post_save.connect(process_tags, sender=Post)

class Author(models.Model):

    user = models.ForeignKey(User)

    bio = MarkupField(default="", blank=True, renderer=render)


class Tag(models.Model):

    blog = models.ForeignKey("Blog")
    name = models.CharField("Tag name", max_length=100)
    slug = models.SlugField(max_length=100, db_index=True)

    template = models.CharField("Template", max_length=100, blank=True)

    count = models.IntegerField(default=0, editable=False)

    description = MarkupField(default="", blank=True, renderer=render)

    def get_summary(self):
        if self.description_summary_html:
            return self.description_summary_html
        else:
            return self.description_html


    def decrement(self):
        count = self.count
        if count:
            count -= 1
            self.count = count
        return count

    def increment(self):
        self.count += 1
        return self.count

    def __unicode__(self):
        return "%s (in %s)" % (self.name, self.blog)

    def posts(self):

        now = datetime.datetime.now()
        posts = self.post_set.filter( published=True,
                                        display_time__lte=now,
                                        version="live",
                                         ).order_by('-display_time')
        return posts

    @models.permalink
    def get_absolute_url(self):
        return ("blog_tag", (),
                dict(blog_slug=self.blog.slug, tag_slug=self.slug))

    def get_blog_relative_url(self):

        return "tag/%s/" % self.slug


    def get_feed(self):
        import feeds
        title = "RSS Feed for %s posts in %s" % (self.name, self.blog.title)
        url = feeds.BlogTagFeed.get_url(self)
        return dict(title=title, url=url)


class ChannelTag(object):

    def __init__(self, channel_slug, tag_slug):
        self.tag_slug = tag_slug
        self.tags = Tag.objects.filter(slug=self.tag_slug)
        self.channel = Channel.objects.get(slug=channel_slug)
        self.description_data = {}
        if not self.tags.count():
            raise Tag.DoesNotExist

    def posts(self):

        query = models.Q()
        for tag in self.tags:
            query = query | models.Q(id__in = tag.post_set.values('pk').query)
        posts = Post.published_posts.filter(query).order_by('-display_time')

        return posts

    def get_feed(self):
        import feeds
        name = Tag.objects.filter(slug=self.tag_slug)[0].name
        title = "RSS Feed for %s posts in %s" % (name, self.channel.title)
        url = feeds.ChannelTagFeed.get_url(self)
        return dict(title=title, url=url)

    def get_absolute_url(self):
        try:
            return reverse("apps.blog.views.tag", kwargs=dict(blog_slug=self.channel.slug, tag_slug=self.tag_slug))
        except Exception, e:
            pass

    def __getattr__(self, attr):
        return getattr(self.tags[0], attr)



class Channel(models.Model):

    template = models.CharField("Template", max_length=100, blank=True)

    title = models.CharField("Channel Title", max_length=100)
    tagline = models.CharField("Tag line", max_length=200)
    slug = models.SlugField(max_length=100, db_index=True)
    posts_per_page = models.IntegerField(default=10)

    template = models.CharField("Template prefix", max_length=100, blank=True)

    description = MarkupField(default="", renderer=render, blank=True)

    blogs = models.ManyToManyField("Blog")

    def is_channel(self):
        """ Returns True if this is a channel (for the benefit of tempalates) """
        return True

    def child_blogs(self):
        return list(self.blogs.order_by('title'))

    def get_full_template_name(self, template_name):
        return self.template.rstrip('/') + '/' + self.template

    def get_template_names(self, template_name):
        template_prefix = self.template.rstrip('/')
        return [template_prefix + '/' + template_name, 'theme/'+template_name, template_name]


    def __unicode__(self):
        return self.title

    def posts(self):
        now = datetime.datetime.now()

        posts = Post.objects.filter( blog__in = self.blogs.all(),
                                     published=True,
                                     version="live",
                                     display_time__lte=now).order_by("-display_time")
        return posts


    def get_tag(self, tag_slug):

        channel_tag = ChannelTag(self.slug, tag_slug)
        return channel_tag


    def tags(self):

        tags = []
        for blog in self.blogs.all():
            tags += list(blog.tags())
        tags.sort(key=lambda t:t.slug)

        collated_tags = []
        for tag_slug, similar_tags in groupby(tags, lambda t:t.slug):
            similar_tags = list(similar_tags)
            channel_tag = ChannelTag(self.slug, tag_slug)

            channel_tag.slug = tag_slug
            channel_tag.name = similar_tags[0].name
            channel_tag.description = similar_tags[0].description
            channel_tag.count = sum(tag.count for tag in similar_tags)

            collated_tags.append(channel_tag)

        collated_tags.sort(key=lambda t:-t.count)

        return collated_tags


    def get_tag_cloud(self, tag_count=30):

        return TagCloud(self, max_tags=tag_count)


    @models.permalink
    def get_absolute_url(self):

        channel_slug = self.slug

        return ("blog_front", (),
                dict(blog_slug=channel_slug))

    def get_feed(self):
        import feeds
        title = "%s RSS Feed"%self.title
        url = feeds.ChannelFeed.get_url(self)
        return dict(title=title, url=url)

    def get_template_names(self, template_name, alternates=None):

        alternates = alternates or []

        alternates = [os.path.join(p, template_name) for p in alternates]

        templates = []
        templates += alternates
        templates.append(os.path.join('blog', template_name))

        return templates


class TagCloud(object):

    def __init__(self, blog, max_tags = 30):

        self.blog = blog

        #self.tags = list( Tag.objects.filter(blog=blog).order_by("-count") )
        self.tags = list(blog.tags())
        if max_tags is not None:
            self.tags = self.tags[:max_tags]

        self.min_font = 12.0
        self.max_font = 20.0

    def set_scale(min_font, max_font):

        self.min_font = min_font
        self.max_font = max_font

    def __iter__(self):

        tag_counts = [tag.count for tag in self.tags]

        sorted_counts = sorted(list(set(tag_counts)))
        # tag_counts = [sorted_counts.index(count) for count in tag_counts]

        places = [sorted_counts.index(tag.count) for tag in self.tags]

        if not places:
            return

        max_count = max(places)
        min_count = min(places)
        count_range = float(max_count - min_count)

        font_size_range = self.max_font - self.min_font

        tag_cloud = []
        for place, tag in zip(places, self.tags):

            tag_scale = (place - min_count) / (count_range or 1.0)
            tag_scale = int(round(tag_scale * 10))

            tag_cloud.append( (tag_scale, tag) )

        #tag_cloud = tag_cloud[::2][::-1] + tag_cloud[1::2]
        #tag_cloud = tag_cloud[::-1]

        for size_tag in tag_cloud:
            yield size_tag


class Blog(models.Model):

    owner = models.ForeignKey(User)

    created_time = models.DateTimeField(auto_now_add=True)

    title = models.CharField("Title of the Blog", max_length=100)
    tagline = models.CharField("Tag line", max_length=200, blank=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    posts_per_page = models.IntegerField(default=10)

    template = models.CharField("Template path", max_length=100)

    description = MarkupField(default="", renderer=render, blank=True)

    def get_full_template_name(self, template_name):
        return self.template.rstrip('/') + '/' + self.template

    def get_template_names(self, template_name, alternates=None):

        alternates = alternates or []

        alternates = [os.path.join(p, template_name) for p in alternates]

        templates = []
        templates += alternates
        templates.append(os.path.join('blog', template_name))

        return templates


    def __unicode__(self):
        return self.title

    def posts(self):
        now = datetime.datetime.now()
        posts = self.post_set.filter(published=True,
                                     version="live",
                                     display_time__lte=now).order_by("-display_time")
        return posts

    def get_tag(self, tag_slug):
        return Tag.objects.get(blog=self, slug=tag_slug)

    def tags(self):
        return self.tag_set.all().order_by("-count")

    @models.permalink
    def get_absolute_url(self):

        blog_slug = self.slug

        return ("blog_front", (),
                dict(blog_slug=blog_slug))

    def get_tag_cloud(self, tag_count=30):

        return TagCloud(self, max_tags=tag_count)


    def get_feed(self):
        import feeds
        title = "%s RSS Feed"%self.title
        url = feeds.BlogFeed.get_url(self)
        return dict(title=title, url=url)

class PublisedPostManager(models.Manager):

    def get_query_set(self):
        posts = super(PublisedPostManager, self).get_query_set()
        now = datetime.datetime.now()
        posts = posts.filter(published=True, display_time__lt=now, version="live")

        return posts

class Post(models.Model):

    blog = models.ForeignKey(Blog)

    title = models.CharField("Post Title", max_length=100)
    slug = models.SlugField("Post Slug", max_length=100, db_index=True)
    published = models.BooleanField("Published?", default=False)
    guid = models.CharField(max_length=255, blank=True)

    allow_comments = models.BooleanField("Allow Comments?", default=True)
    show_comments = models.BooleanField("Show Comments?", default=True)

    series = models.CharField("Series name", max_length=100, blank=True, default="")
    source = models.CharField("Post source", max_length=100, blank=True, default="")

    created_time = models.DateTimeField(auto_now_add=True)
    edit_time = models.DateTimeField(auto_now=True)
    display_time = models.DateTimeField("Display Time", default=datetime.datetime.now)

    tags = models.ManyToManyField("Tag", blank=True)

    tags_text = models.TextField("Comma separated tags", default="", blank=True)

    content = MarkupField(default="", renderer=render, blank=True)

    version = models.CharField("Version", max_length=100, default="live")
    version_id = models.IntegerField("Parent Post ID", blank=True, null=True)

    template_path = models.CharField("Template path (blank for default)", max_length=100, default="", blank=True)

    #created_time = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    published_posts = PublisedPostManager()

    def get_tags(self):
        return self.tags.filter(count__gt=0)

    def get_template_names(self, name="default"):

        templates = []
        if self.template_path:
            templates.append( os.path.join(self.template_path, name) )

        templates.append( os.path.join("blog/posts/", name) )
        return templates

    def is_series(self):
        return bool(self.series)

    def get_series(self):
        posts = Post.objects.filter(series=self.series).order_by('display_time')
        index_posts = [(i+1, post) for i, post in enumerate(posts)]

        current_part = None
        for i, post in index_posts:
            if post is self:
                current_part = i
                break

        return index_posts, current_part

    def get_summary(self):
        if self.content_summary_html:
            return self.content_summary_html
        else:
            return self.content_html

    def get_admin_abbrev(self):
        if len(self.content_text) < 100:
            return self.content_text
        return self.content_text[:100]+" [...]"
    get_admin_abbrev.short_description = "Content (abbreviated)"

    def get_admin_html(self):
        return self.html
    get_admin_html.allow_tags = True

    def __unicode__(self):
        if self.version == 'live':
            return self.title
        return "%s [%s]" % (self.title, self.version.upper())

    def date_url(self):
        year = self.display_time.year
        month = self.display_time.month
        day = self.display_time.day
        return "%d/%d/%d/%s" % (year, month, day, self.slug)

    @models.permalink
    def get_absolute_url(self):

        blog_slug = self.blog.slug

        slug = self.slug
        if '|' in slug:
            slug = slug.split('|', 1)[-1]

        year = self.display_time.year
        month = self.display_time.month
        day = self.display_time.day

        return ("blog_post", (),
                dict(blog_slug=blog_slug, year=year, month=month, day=day, slug=slug))

    def get_blog_relative_url(self):

        year = self.display_time.year
        month = self.display_time.month
        day = self.display_time.day

        return "%i/%i/%i/%s/" % (year, month, day, self.slug)


    def _remove_tags(self):

        if self.pk is not None:

            if self.version != 'live':
                return
            tags = Tag.objects.filter(blog=self.blog, post=self)
            for tag in self.tags.all():
                tag.decrement()
                tag.save()
                self.tags.remove(tag)


    def _add_tags(self):

        """Creates tags or increments tag counts as neccesary.

        """

        if self.version != 'live':
            return

        tags = [t.strip() for t in self.tags_text.split(',')]
        tags = list(set(tags))

        for tag_name in tags:
            tag_slug = slugify(tag_name)
            if tag_slug:
                try:
                    tag = Tag.objects.get(blog=self.blog, slug=tag_slug)
                except Tag.DoesNotExist:
                    tag = Tag( blog = self.blog,
                               name = tag_name,
                               slug = tag_slug)

                tag.increment()
                tag.save()

                self.tags.add(tag)

    def delete(self, *args, **kwargs):
        self._remove_tags()
        super(Post, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):

        self._remove_tags()
        super(Post, self).save(*args, **kwargs)
        self._add_tags()
        if self.version == 'live' and self.published:
            broadcast.safe_first.new_content_on_site()

    def get_tags(self):

        tags = list(self.tags.all())
        tags.sort(key=lambda t:t.name.lower())
        return tags

    def is_new(self):

        age = datetime.datetime.now() - self.display_time
        return age.days < 7


    def get_parent_version(self):

        if self.version_id is None:
            return self
        parent_post = Post.objects.get(self.version_id)
        return parent_post


    def get_version(self, version):

        """Creates a draft post that can be used for previews."""

        if self.version == version:
            return self

        #version_slug = self.get_version_slug(version)

        parent_version_id = self.get_parent_version().id

        try:
            versioned_post = Post.objects.get(blog=self.blog, version_id=parent_version_id, version=version)
            return versioned_post
        except Post.DoesNotExist:
            versioned_post = Post(version_id=parent_version_id, published=False, blog=self.blog, version=version)
            versioned_post.save()

        copy_attribs = ['title',
                        'tags_text',
                        'content',
                        'content_markup_type',
                        'allow_comments',
                        'published',
                        'display_time',
                        'slug']

        for attrib in copy_attribs:
            setattr(versioned_post, attrib, getattr(self, attrib))
        versioned_post.save()

        return versioned_post

    def delete_version(self, version):

        """Removes the draft object associated with a post."""

        parent_version_id = self.get_parent_version().id

        try:
            versioned_post = Post.objects.get(blog=self.blog,
                                              version_id=parent_version_id,
                                              version=version)
            versioned_post.delete()
        except Post.DoesNotExist:
            pass

    def version_exists(self, version):

        parent_version_id = self.get_parent_version().id

        try:
            versioned_post = Post.objects.get(blog=self.blog, version_id=parent_version_id, version=version)
            return True
        except Post.DoesNotExist:
            return False



    def get_related_posts(self, count=10):

        post = self
        if post.version != "live":
            slug = self.slug.split('|', 1)[-1]
            try:
                post = Post.objects.get(slug=slug, version="live")
            except Post.DoesNotExist:
                pass
        blog = post.blog

        tags = list(post.tags.all())

        posts = Post.objects.filter(blog=blog, tags__in=tags).exclude(pk=post.id).order_by('-display_time')[:1000]

        def count_iter(i):
            return sum(1 for _ in i)

        counts_and_posts = [(post, count_iter(similar_posts)) for post, similar_posts in groupby(posts)]

        if counts_and_posts:
            max_count = max(counts_and_posts, key=lambda c:c[1])[1]
            min_count = min(counts_and_posts, key=lambda c:c[1])[1]

            if min_count != max_count:
                counts_and_posts = [cap for cap in counts_and_posts if cap[1] != min_count]

        counts_and_posts.sort(key=lambda i:(i[1], i[0].display_time))
        return [cp[0] for cp in reversed(counts_and_posts[-count:])]

class Microblog(models.Model):

    enabled = models.BooleanField("Enabled?", default=True)

    blog = models.ForeignKey(Blog)
    service = models.CharField("Service", max_length=100, default="twitter", blank=True)
    tags = models.CharField("Tags", max_length=200)
    url = models.CharField("Url", max_length=255, default="", blank=True)
    username = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=100, blank=True)
    poll_minutes = models.IntegerField(default=10)
    template_path = models.CharField(max_length=255)

    next_poll_time = models.DateTimeField("Time to next poll", auto_now_add=True)
