from django.contrib.auth.models import User
from django.db import models
from django.conf import settings

import os
import os.path

import Image

# Create your models here.

class ImageUpload(models.Model):

    owner = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="uploads/images")
    description = models.TextField(default="")

    def thumb(self, width=None, height=None):

        if width is None and height is None:
            return self.image.url

        image = Image.open(self.image.path)
        w, h = image.size

        aspect = float(w)/h

        thumb_width = width
        thumb_height = height

        if thumb_width is None:
            thumb_width = thumb_height * aspect
        elif thumb_height is None:
            thumb_height = thumb_width / aspect

        thumb_width = int(thumb_width)
        thumb_height = int(thumb_height)

        dirname, filename = os.path.split(self.image.path)

        try:
            os.mkdir(os.path.join(dirname, 'thumbs'))
        except OSError:
            pass

        filename, ext = os.path.splitext(filename)
        thumb_size_suffix = "_%dx%d" % (thumb_width, thumb_height)

        thumb_filename = filename+thumb_size_suffix+".jpg"

        thumb_path = os.path.join(dirname, 'thumbs', filename+thumb_size_suffix+".jpg")

        if not os.path.exists(thumb_path):

            image.thumbnail((thumb_width, thumb_height), Image.ANTIALIAS)
            image.save(thumb_path, quality=85)

        url = settings.MEDIA_URL + "uploads/images/thumbs/" + thumb_filename

        return url, (thumb_width, thumb_height)

    def thumbnail_html(self):
        WIDTH = 100
        url, (w, h) = self.thumb(WIDTH)
        full_url = settings.MEDIA_URL + self.image.name

        html = '<a href="%s" target="_blank"><img src="%s" width="%i" height="%i" /></a>' % \
            (full_url, url, w, h)

        return html
    
    thumbnail_html.allow_tags = True



class FileUpload(models.Model):

    owner = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    data = models.ImageField(upload_to="uploads/files")
    description = models.TextField(default="")