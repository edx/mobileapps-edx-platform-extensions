from django.conf.urls import patterns, url
from mobileapps import views as mobile_views


urlpatterns = patterns(
    '',
    url(r'^$', mobile_views.MobileAppView.as_view(), name='mobileapps'),
    url(r'^(?P<pk>[0-9]+)$', mobile_views.MobileAppDetailView.as_view(), name='mobileapps-detail'),
    url(r'^(?P<mobileapp_id>[0-9]+)/users$', mobile_views.MobileAppUserView.as_view(), name='mobileapps-users'),
    url(r'^(?P<mobileapp_id>[0-9]+)/organizations$',
        mobile_views.MobileAppOrganizationView.as_view(), name='mobileapps-organizations'),
)
