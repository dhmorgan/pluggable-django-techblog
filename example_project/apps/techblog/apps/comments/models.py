from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from techblog.markup.fields import MarkupField

from techblog import broadcast



def _comment_renderer(markup, markup_type):

    html, summary_html, text, data = broadcast.call.render_comment(markup, markup_type)
    return html, summary_html, text, data

class CommentManager(models.Manager):

    def filter_for_object(self, object):
        ct = ContentType.objects.get_for_model(object)
        comments = Comment.objects.filter(object_id=object.id, content_type=ct, visible=True, moderated=True)
        return comments

    def filter_for_model(self, model):
        ct = ContentType.objects.get_for_model(model)
        comments = Comment.objects.filter(content_type=ct, visible=True, moderated=True)
        return comments

class Comment(models.Model):

    objects = CommentManager()

    content_type = models.ForeignKey(ContentType, db_index=True)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    visible = models.BooleanField(default=False)
    moderated = models.BooleanField(default=False)

    created_time = models.DateTimeField(auto_now_add=True)

    type = models.CharField("Type of comment", max_length=100, blank=True)
    owner = models.ForeignKey(User, blank=True, null=True, default=None)
    group = models.CharField("Optional comment group", max_length=100, blank=True, default="")

    name = models.CharField("Author's name", max_length=100)
    email = models.EmailField("Author's email", blank=True)
    url = models.CharField(blank=True, default="", max_length=255)
    content = MarkupField(default="", renderer=_comment_renderer)

    def __unicode__(self):
        return self.name



    def site_link(self):
        object_url = self.object_url() + '#comment' +str(self.id)
        url = '''<a href="%s">comment by %s</a>''' % (object_url, self.name)
        return url
    site_link.allow_tags = True

    def object_url(self):
        return self.content_object.get_absolute_url()

    def comment_object_description(self):
        return unicode(self.content_object)
