"""
Django database models supporting the mobile apps
"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


from edx_solutions_organizations.models import Organization
from model_utils.models import TimeStampedModel
from model_utils.fields import AutoCreatedField
from edx_solutions_api_integration.utils import StringCipher


OS_CHOICES = (
    (1, 'Android'),
    (2, 'iOS'),
    (3, 'Windows'),
    (4, 'Other'),
)

DEPLOYMENT_CHOICES = (
    (1, 'Public app store'),
    (2, 'Enterprise'),
    (3, 'OTA'),
    (4, 'Other'),
)


class NotificationProvider(TimeStampedModel):
    """
    A django model to track notification providers.
    """
    name = models.CharField(max_length=255)
    api_url = models.CharField(max_length=255, null=True, blank=True)


class MobileApp(TimeStampedModel):
    """
    A django model to track mobile apps.
    """
    identifier = models.CharField(max_length=255, db_index=True, unique=True)
    name = models.CharField(max_length=255)
    operating_system = models.PositiveSmallIntegerField(choices=OS_CHOICES)
    deployment_mechanism = models.PositiveSmallIntegerField(choices=DEPLOYMENT_CHOICES, default=1)
    download_url = models.CharField(max_length=255, null=True, blank=True)
    analytics_url_dev = models.CharField(max_length=255, null=True, blank=True)
    analytics_url_prod = models.CharField(max_length=255, null=True, blank=True)
    notification_provider = models.ForeignKey(NotificationProvider, related_name="mobile_apps", blank=True, null=True)
    provider_key = models.CharField(max_length=255, null=True, blank=True)
    provider_secret = models.CharField(max_length=255, null=True, blank=True)
    provider_dashboard_url = models.CharField(max_length=255, null=True, blank=True)
    current_version = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, blank=True)
    users = models.ManyToManyField(User, related_name="mobile_apps", blank=True)
    organizations = models.ManyToManyField(Organization, related_name="mobile_apps", blank=True)

    @property
    def provider_key_decrypted(self):
        if self.provider_key:
            return StringCipher.decrypt(self.provider_key.encode())

    @property
    def provider_secret_decrypted(self):
        if self.provider_secret:
            return StringCipher.decrypt(self.provider_secret.encode())


class MobileAppHistory(models.Model):
    """
    A django model to track changes in mobile app model.
    """
    identifier = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255)
    operating_system = models.PositiveSmallIntegerField(choices=OS_CHOICES)
    deployment_mechanism = models.PositiveSmallIntegerField(choices=DEPLOYMENT_CHOICES)
    download_url = models.CharField(max_length=255, null=True, blank=True)
    analytics_url_dev = models.CharField(max_length=255, null=True, blank=True)
    analytics_url_prod = models.CharField(max_length=255, null=True, blank=True)
    notification_provider = models.ForeignKey(NotificationProvider, blank=True, null=True, on_delete=models.PROTECT)
    provider_key = models.CharField(max_length=255, null=True, blank=True)
    provider_secret = models.CharField(max_length=255, null=True, blank=True)
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
    mobile_app_history.identifier = mobile_app.identifier
    mobile_app_history.name = mobile_app.name
    mobile_app_history.operating_system = mobile_app.operating_system
    mobile_app_history.deployment_mechanism = mobile_app.deployment_mechanism
    mobile_app_history.download_url = mobile_app.download_url
    mobile_app_history.analytics_url_dev = mobile_app.analytics_url_dev
    mobile_app_history.analytics_url_prod = mobile_app.analytics_url_prod
    mobile_app_history.notification_provider = mobile_app.notification_provider
    mobile_app_history.provider_key = mobile_app.provider_key
    mobile_app_history.provider_secret = mobile_app.provider_secret
    mobile_app_history.provider_dashboard_url = mobile_app.provider_dashboard_url
    mobile_app_history.current_version = mobile_app.current_version
    mobile_app_history.is_active = mobile_app.is_active
    mobile_app_history.updated_by = mobile_app.updated_by
    mobile_app_history.save()
