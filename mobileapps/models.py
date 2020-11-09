"""
Django database models supporting the mobile apps
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from edx_solutions_api_integration.utils import StringCipher
from edx_solutions_organizations.models import Organization
from mobileapps.image_helpers import get_image_names, remove_images
from model_utils.fields import AutoCreatedField
from model_utils.models import TimeStampedModel

DEPLOYMENT_CHOICES = (
    (1, 'Public app store'),
    (2, 'Enterprise'),
    (3, 'OTA'),
    (4, 'Other'),
)


class EncryptedCharField(models.CharField):
    prefix = 'enc_str__'

    def from_db_value(self, value, expression, connection, context):
        if value and value.startswith(self.prefix):
            value = StringCipher.decrypt(value[len(self.prefix):].encode())
        return value.decode('utf-8') if value else None

    def get_db_prep_value(self, value, connection, prepared=False):
        if value and not value.startswith(self.prefix):
            value = self.prefix + StringCipher.encrypt(value)
        return value


class NotificationProvider(TimeStampedModel):
    """
    A django model to track notification providers.
    """
    name = models.CharField(max_length=255)
    api_url = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.name


class MobileApp(TimeStampedModel):
    """
    A django model to track mobile apps.
    """
    name = models.CharField(max_length=255)
    ios_app_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    ios_bundle_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    android_app_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    ios_download_url = models.CharField(max_length=255, null=True, blank=True)
    android_download_url = models.CharField(max_length=255, null=True, blank=True)
    deployment_mechanism = models.PositiveSmallIntegerField(choices=DEPLOYMENT_CHOICES, default=1)
    analytics_url = models.CharField(max_length=255, null=True, blank=True)
    notification_provider = models.ForeignKey(NotificationProvider, related_name="mobile_apps", blank=True, null=True, on_delete=models.CASCADE)
    provider_key = EncryptedCharField(max_length=255, null=True, blank=True)
    provider_secret = EncryptedCharField(max_length=255, null=True, blank=True)
    provider_dashboard_url = models.CharField(max_length=255, null=True, blank=True)
    current_version = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, blank=True)
    users = models.ManyToManyField(User, related_name="mobile_apps", blank=True)
    organizations = models.ManyToManyField(Organization, related_name="mobile_apps", blank=True)

    @property
    def deployment_mechanism_choice_text(self):
        return dict(DEPLOYMENT_CHOICES)[self.deployment_mechanism]

    def get_api_keys(self):
        return {
            'provider_key': self.provider_key,
            'provider_secret': self.provider_secret,
        }

    def get_notification_provider_name(self):
        """
        this function returns notification provider name against a given mobile app
        if provider is not available it will return None
        """
        notification_provider = self.notification_provider
        if notification_provider:
            return notification_provider.name
        return None


class MobileAppHistory(models.Model):
    """
    A django model to track changes in mobile app model.
    """
    name = models.CharField(max_length=255)
    ios_app_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    ios_bundle_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    android_app_id = models.CharField(max_length=255, db_index=True, null=True, blank=True)
    ios_download_url = models.CharField(max_length=255, null=True, blank=True)
    android_download_url = models.CharField(max_length=255, null=True, blank=True)
    deployment_mechanism = models.PositiveSmallIntegerField(choices=DEPLOYMENT_CHOICES)
    analytics_url = models.CharField(max_length=255, null=True, blank=True)
    notification_provider = models.ForeignKey(NotificationProvider, blank=True, null=True, on_delete=models.PROTECT)
    provider_key = EncryptedCharField(max_length=255, null=True, blank=True)
    provider_secret = EncryptedCharField(max_length=255, null=True, blank=True)
    provider_dashboard_url = models.CharField(max_length=255, null=True, blank=True)
    current_version = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = AutoCreatedField()


@receiver(post_save, sender=MobileApp)
def user_post_save_callback(sender, **kwargs):
    """
    Save mobile app history after saving the mobile app data.
    """
    mobile_app = kwargs['instance']
    mobile_app_history = MobileAppHistory()
    mobile_app_history.name = mobile_app.name
    mobile_app_history.ios_app_id = mobile_app.ios_app_id
    mobile_app_history.ios_bundle_id = mobile_app.ios_bundle_id
    mobile_app_history.android_app_id = mobile_app.android_app_id
    mobile_app_history.ios_download_url = mobile_app.ios_download_url
    mobile_app_history.android_download_url = mobile_app.android_download_url
    mobile_app_history.deployment_mechanism = mobile_app.deployment_mechanism
    mobile_app_history.analytics_url = mobile_app.analytics_url
    mobile_app_history.notification_provider = mobile_app.notification_provider
    mobile_app_history.provider_key = mobile_app.provider_key
    mobile_app_history.provider_secret = mobile_app.provider_secret
    mobile_app_history.provider_dashboard_url = mobile_app.provider_dashboard_url
    mobile_app_history.current_version = mobile_app.current_version
    mobile_app_history.is_active = mobile_app.is_active
    mobile_app_history.updated_by = mobile_app.updated_by
    mobile_app_history.save()


class Theme(TimeStampedModel):
    """
    A django model to store theme for organizations.
    """
    name = models.CharField(max_length=255, null=True, blank=True)
    logo_image_uploaded_at = models.DateTimeField(db_index=True, null=True, blank=True)
    header_bg_image_uploaded_at = models.DateTimeField(db_index=True, null=True, blank=True)
    organization = models.ForeignKey(Organization, related_name="theme", on_delete=models.CASCADE)
    header_background_color = models.CharField(max_length=255, null=True, blank=True)
    navigation_text_color = models.CharField(max_length=255, null=True, blank=True)
    navigation_icon_color = models.CharField(max_length=255, null=True, blank=True)
    completed_course_tint = models.CharField(max_length=255, null=True, blank=True)
    lesson_navigation_color = models.CharField(max_length=255, null=True, blank=True)
    active = models.NullBooleanField(default=None)

    class Meta:
        unique_together = (('organization', 'active'), )

    def delete(self):
        self.remove_logo_image()
        self.remove_header_bg_image()
        super().delete()

    @staticmethod
    def mark_existing_as_inactive(organization_id):
        try:
            theme = Theme.objects.get(organization_id=organization_id, active=True)
            theme.active = None
            theme.save(update_fields=['active'])
        except Theme.DoesNotExist:
            pass

    def remove_logo_image(self):
        image_names = get_image_names(
            settings.ORGANIZATION_THEME_IMAGE_SECRET_KEY,
            "{}-{}-{}".format(self.organization.name, self.id, settings.ORGANIZATION_LOGO_IMAGE_KEY_PREFIX),
            list(settings.ORGANIZATION_LOGO_IMAGE_SIZES_MAP.values())
        )
        remove_images(settings.ORGANIZATION_LOGO_IMAGE_BACKEND, image_names)
        self.logo_image_uploaded_at = None
        self.save(update_fields=['logo_image_uploaded_at', 'modified'])

    def remove_header_bg_image(self):
        image_names = get_image_names(
            settings.ORGANIZATION_THEME_IMAGE_SECRET_KEY,
            "{}-{}-{}".format(self.organization.name, self.id, settings.ORGANIZATION_HEADER_BG_IMAGE_KEY_PREFIX),
            list(settings.ORGANIZATION_HEADER_BG_IMAGE_SIZES_MAP.values())
        )
        remove_images(settings.ORGANIZATION_LOGO_IMAGE_BACKEND, image_names)
        self.header_bg_image_uploaded_at = None
        self.save(update_fields=['header_bg_image_uploaded_at', 'modified'])
