from django.conf.urls import patterns, url
from mobileapps import views as mobile_views


urlpatterns = patterns(
    '',
    url(r'^notification_providers$', mobile_views.NotificationProviderView.as_view(), name='notification_providers'),
    url(r'^$', mobile_views.MobileAppView.as_view(), name='mobileapps'),
    url(r'^(?P<pk>[0-9]+)$', mobile_views.MobileAppDetailView.as_view(), name='mobileapps-detail'),
    url(r'^(?P<mobile_app_id>[0-9]+)/users$', mobile_views.MobileAppUserView.as_view(), name='mobileapps-users'),
    url(r'^(?P<mobile_app_id>[0-9]+)/organizations$',
        mobile_views.MobileAppOrganizationView.as_view(), name='mobileapps-organizations'),
    url(r'^(?P<mobile_app_id>[0-9]+)/notification$', mobile_views.MobileAppAllUsersNotifications.as_view(),
        name='mobileapps-all-users-notifications'),
    url(r'^(?P<mobile_app_id>[0-9]+)/users/notification$', mobile_views.MobileAppSelectedUsersNotifications.as_view(),
        name='mobileapps-selected-users-notifications'),
    url(r'^(?P<mobile_app_id>[0-9]+)/organization/(?P<organization_id>[0-9]+)/notification$',
        mobile_views.MobileAppOrganizationAllUsersNotifications.as_view(),
        name='mobileapps-organization-all-users-notifications'),
)
