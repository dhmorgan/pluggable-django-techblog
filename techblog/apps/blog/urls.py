import views
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from feeds import BlogFeed, BlogTagFeed

feeds = {
    'posts': BlogFeed,
    'tag' : BlogTagFeed
}


urlpatterns = patterns('',

    url(r'^xhr/preview_comment/$', views.xhr_preview_comment, name="xhr_preview_comment"),

    url(r'^tools/import/$', views.import_wxr, name='import_wxr'),
    url(r'^feeds/(?P<feed_item>.+)/$', views.feeds, {'feed_dict': feeds}, name="blog_feeds"),

    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[\w-]*)/$', views.blog_post, name="blog_post"),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/$', views.blog_month, name="blog_month"),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/page/(?P<page_no>\d+)/$', views.blog_month, name="blog_month_with_page"),

    url(r'^tag/(?P<tag_slug>[\w-]*)/$', views.tag, name="blog_tag"),
    url(r'^tag/(?P<tag_slug>[\w-]*)/page/(?P<page_no>\d+)/$', views.tag, name="blog_tag_with_page" ),

    url(r'^page/(?P<page_no>\d+)/$', views.blog_front, name="blog_front_with_page"),
    url(r'^search/$', views.blog_search, name="blog_search"),

    url(r'^writer/(?P<post_id>\d+)/$', views.writer, name="writer"),
    url(r'^newpost/$', views.newpost, name="newpost"),
    url(r'^manage/$', views.manage, name="manage"),

    url(r'^$', views.blog_front, name="blog_front"),

    )