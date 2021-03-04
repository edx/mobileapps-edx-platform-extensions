from django.conf import settings
from mobileapps.image_helpers import get_image_urls_by_key
from mobileapps.models import (DEPLOYMENT_CHOICES, MobileApp,
                               NotificationProvider, Theme)
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from rest_framework import serializers


class NotificationProviderSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = NotificationProvider


class MobileAppSerializer(serializers.ModelSerializer):
    deployment_mechanism = serializers.ChoiceField(choices=DEPLOYMENT_CHOICES, required=False)

    class Meta:
        model = MobileApp
        fields = '__all__'
        extra_kwargs = {'updated_by': {'read_only': True}}

    def _set_custom_validated_data(self, validated_data):
        """
        Here we are adding current user in 'updated_by' field
        """
        validated_data['updated_by'] = self.context['request'].user

    def create(self, validated_data):
        self._set_custom_validated_data(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._set_custom_validated_data(validated_data)
        return super().update(instance, validated_data)


class BasicMobileAppSerializer(MobileAppSerializer):
    class Meta:
        model = MobileAppSerializer.Meta.model
        fields = ('name', 'ios_app_id', 'android_app_id', 'ios_download_url', 'android_download_url', 'ios_bundle_id',
                  'deployment_mechanism', 'current_version', 'is_active')


class ThemeSerializer(serializers.ModelSerializer):
    logo_image = serializers.SerializerMethodField()
    header_bg_image = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = Theme

    def get_logo_image(self, theme):
        return get_image_urls_by_key(
            settings.ORGANIZATION_THEME_IMAGE_SECRET_KEY,
            "{}-{}-{}".format(theme.organization.name, theme.id, settings.ORGANIZATION_LOGO_IMAGE_KEY_PREFIX),
            theme.logo_image_uploaded_at,
            settings.ORGANIZATION_LOGO_IMAGE_SIZES_MAP,
            settings.ORGANIZATION_LOGO_IMAGE_BACKEND,
            False,
        )

    def get_header_bg_image(self, theme):
        return get_image_urls_by_key(
            settings.ORGANIZATION_THEME_IMAGE_SECRET_KEY,
            "{}-{}-{}".format(theme.organization.name, theme.id, settings.ORGANIZATION_HEADER_BG_IMAGE_KEY_PREFIX),
            theme.header_bg_image_uploaded_at,
            settings.ORGANIZATION_HEADER_BG_IMAGE_SIZES_MAP,
            settings.ORGANIZATION_LOGO_IMAGE_BACKEND,
            False,
        )


class BasicThemeSerializer(ThemeSerializer):
    """ Serializer for Theme without organization data """

    class Meta:
        model = ThemeSerializer.Meta.model
        exclude = ('organization',)
