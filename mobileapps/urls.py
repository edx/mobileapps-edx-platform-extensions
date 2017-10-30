from django.conf.urls import patterns, url
from mobileapps import views as mobile_views


urlpatterns = patterns(
    '',
    url(r'^$', mobile_views.MobileAppView.as_view(), name='mobileapps'),
    url(r'^(?P<pk>[0-9]+)$', mobile_views.MobileAppDetailView.as_view(), name='mobileapps-detail'),
)
