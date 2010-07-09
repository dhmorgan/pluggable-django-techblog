import views
from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url(r'^login/$', views.login, name="login" ),
    url(r'^logout/$', views.logout, name="logout" ),
)
