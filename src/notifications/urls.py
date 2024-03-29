from django.conf.urls import  url

from notifications import views

urlpatterns = [
    url(r'^$', views.list, name='list'), # function based view
    url(r'^unread/$', views.list_unread, name='list_unread'), # function based view
    url(r'^ajax/$', views.ajax, name='ajax'), # function based view
    url(r'^read/(?P<id>\d+)/$', views.read, name='read'), # function based view
    url(r'^read/all/$', views.read_all, name='read_all'), # function based view
    # url(r'^options/$', views.options, name='options'), # function based view
]
