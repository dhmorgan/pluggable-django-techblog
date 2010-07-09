from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from apps.blog.sitemap import PostSitemap, TagSitemap, BlogSitemap, ChannelSitemap, RootblogSitemap, RootblogPostSitemap
from apps.pages.sitemap import PageSitemap

sitemaps = { 'blogs' : BlogSitemap,
             'channels' : ChannelSitemap,
             'rootblog' : RootblogSitemap,
             'posts' : PostSitemap,
             'rootblogposts' : RootblogPostSitemap,
             'pages' : PageSitemap,
             'tags' : TagSitemap }

urlpatterns = patterns('',

    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),

    #url(r'^$', 'apps.blog.views.blog_front', {"blog_slug":"test-blog"}),
)


urlpatterns += patterns('',
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}) )


def bad(request):
    """ Simulates a server error """
    1/0

urlpatterns += patterns('',

    (r'^bad/$', bad),
    (r'^', include('techblog.apps.blog.urls'), {"blog_slug":settings.DEFAULT_BLOG_SLUG, "blog_root":"/"}),

    (r'^blog/(?P<blog_slug>[\w-]*)/', include('techblog.apps.blog.urls') ),

    (r'^comments/', include('techblog.apps.comments.urls')),
    (r'^accounts/', include('techblog.apps.accounts.urls')),
    (r'^sitemap.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    (r'^', include('techblog.apps.pages.urls')),

)
