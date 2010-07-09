#!/usr/bin/env python
from django.contrib import admin

import models



class BlogAdmin(admin.ModelAdmin):
    fields = ('owner',
              'title',
              'slug',
              'tagline',
              'description_markup_type',
              'description',
              'description_html',
              )
    prepopulated_fields = {"slug": ("title",)}
    list_display = ['__unicode__', 'tagline']
    search_fields=('title', 'tagline', 'description')
    radio_fields={'description_markup_type':admin.HORIZONTAL}

admin.site.register(models.Blog, BlogAdmin)


class ChannelAdmin(admin.ModelAdmin):
    fields = ('title',
              'slug',
              'tagline',
              'blogs',
              'description_markup_type',
              'description',
              'description_html',
              )
    prepopulated_fields = {"slug": ("title",)}
    list_display = ['__unicode__', 'tagline']
    search_fields=('title', 'tagline', 'description')
    radio_fields={'description_markup_type':admin.HORIZONTAL}

admin.site.register(models.Channel, ChannelAdmin)


class PostAdmin(admin.ModelAdmin):
    fields = ('blog',
              'title',
              'slug',
              'series',
              'template_path',
              'published',
              'allow_comments',
              'display_time',
              'tags_text',
              'content_markup_type',
              'content',
              'content_html',
              'content_summary_html')
    list_display = ['__unicode__', 'display_time', 'blog']
    list_filter = ('blog', 'display_time', 'published', 'version')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'display_time'
    search_fields=('title', 'tags_text', 'content')
    radio_fields={'content_markup_type':admin.HORIZONTAL}
    ordering=('-display_time', 'title')

admin.site.register(models.Post, PostAdmin)


class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'blog', 'count')
    search_fields= ['name']

admin.site.register(models.Tag, TagAdmin)

class MicroblogAdmin(admin.ModelAdmin):
    fields = ('blog',
              'service',
              'tags',
              'url',
              'username',
              'password',
              'poll_minutes',
              'template_path')

admin.site.register(models.Microblog, MicroblogAdmin)