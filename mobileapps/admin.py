from django.contrib import admin

from mobileapps.models import NotificationProvider, MobileApp


class NotificationProviderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'api_url', 'created')

admin.site.register(NotificationProvider, NotificationProviderAdmin)


class MobileAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'ios_app_id', 'android_app_id', 'created')
    exclude = ('users', 'organizations', 'updated_by',)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        obj.save()


admin.site.register(MobileApp, MobileAppAdmin)
