#!/usr/bin/env python
from django.contrib import admin

import models



class CommentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'site_link', 'comment_object_description', 'created_time', 'moderated', 'visible', 'name', 'email', 'url')
    list_filter = ('created_time', 'moderated', 'visible')

admin.site.register(models.Comment, CommentAdmin)
