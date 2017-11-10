from django.contrib import admin
from .models import NotificationProvider, MobileApp


class NotificationProviderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'api_url', 'created')

admin.site.register(NotificationProvider, NotificationProviderAdmin)


class MobileAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ios_app_id', 'android_app_id', 'created')

admin.site.register(MobileApp, MobileAppAdmin)
