from django.conf.urls import url
from mobileapps import views as mobile_views

urlpatterns = [
    url(r'^notification_providers$', mobile_views.NotificationProviderView.as_view(), name='notification_providers'),
    url(r'^$', mobile_views.MobileAppView.as_view(), name='mobileapps'),
    url(r'^(?P<pk>[0-9]+)$', mobile_views.MobileAppDetailView.as_view(), name='mobileapps-detail'),
    url(r'^(?P<mobile_app_id>[0-9]+)/users$', mobile_views.MobileAppUserView.as_view(), name='mobileapps-users'),
    url(r'^(?P<mobile_app_id>[0-9]+)/organizations$',
        mobile_views.MobileAppOrganizationView.as_view(), name='mobileapps-organizations'),
    url(r'^notification$', mobile_views.MobileAppsNotifications.as_view(), name='mobileapps-notifications'),
    url(r'^(?P<mobile_app_id>[0-9]+)/notification$', mobile_views.MobileAppAllUsersNotifications.as_view(),
        name='mobileapps-all-users-notifications'),
    url(r'^(?P<mobile_app_id>[0-9]+)/users/notification$', mobile_views.MobileAppSelectedUsersNotifications.as_view(),
        name='mobileapps-selected-users-notifications'),
    url(r'^(?P<mobile_app_id>[0-9]+)/organization/(?P<organization_id>[0-9]+)/notification$',
        mobile_views.MobileAppOrganizationAllUsersNotifications.as_view(),
        name='mobileapps-organization-all-users-notifications'),
    url(r'^organization/(?P<organization_id>[0-9]+)/themes$',
        mobile_views.OrganizationThemeView.as_view(),
        name='mobileapps-organization-themes'),
    url(r'^themes/(?P<theme_id>[0-9]+)$',
        mobile_views.OrganizationThemeDetailView.as_view(),
        name='mobileapps-organization-themes-detail'),
    url(r'^themes/(?P<theme_id>[0-9]+)/remove/(?P<attribute>[\w\_]+)$',
        mobile_views.OrganizationThemeRemoveImageView.as_view(),
        name='mobileapps-organization-themes-remove-image'),
]
