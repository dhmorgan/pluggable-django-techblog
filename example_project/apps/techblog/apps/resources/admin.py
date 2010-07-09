from django.contrib import admin

import models


class ImageUploadAdmin(admin.ModelAdmin):
    fields = ( 'owner',
               'name',
              'image',
              'description'
              )
    list_display = ('name', 'thumbnail_html', 'description')
    search_fields = ['name', 'description']


admin.site.register(models.ImageUpload, ImageUploadAdmin)
