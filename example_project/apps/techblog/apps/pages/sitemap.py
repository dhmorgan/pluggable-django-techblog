from django.contrib.sitemaps import Sitemap

from models import Page

from datetime import datetime, timedelta

class PageSitemap(Sitemap):
    priority = 0.5

    def items(self):
        return Page.published_pages.all()

    def lastmod(self, obj):
        return obj.edit_time

    def changefreq(self, obj):

        now = datetime.now()
        days_since = (now - obj.edit_time).days

        if days_since < 1:
            return 'hourly'
        elif days_since < 7:
            return 'daily'
        return 'weekly'

    def location(self, obj):
        return obj.get_absolute_url()
