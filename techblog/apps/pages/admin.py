from django.contrib import admin

import models


class PageBaseAdmin(admin.ModelAdmin):
    fields = (  'name',
                'template' )
    list_display = ['__unicode__', 'template']

admin.site.register(models.PageBase, PageBaseAdmin)


class PageAdmin(admin.ModelAdmin):
    fields = ('base',
              'parent',
              'inherit',
              'title',
              'slug',
              'published',
              'promoted',
              'allow_comments',
              'show_comments',
              'content_markup_type',
              'content',
              )

    radio_fields={'content_markup_type':admin.HORIZONTAL}
    list_display = ['__unicode__', 'base', 'published']
    search_fields=('title', )
    prepopulated_fields = {"slug": ("title",)}

admin.site.register(models.Page, PageAdmin)