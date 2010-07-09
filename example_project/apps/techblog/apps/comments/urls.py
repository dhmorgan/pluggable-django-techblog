import views
from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url('^xhr/post/$', views.xhr_post_comment, name='xhr_post_comment'),
    url('^xhr/delete/$', views.xhr_delete_comment, name='xhr_delete_comment'),
    url('^success/$', views.post_success, name="post_success"),
                       )
