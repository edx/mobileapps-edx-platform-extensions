from rest_framework import serializers

from mobileapps.image_helpers import get_logo_image_urls_by_organization_name
from mobileapps.models import MobileApp, NotificationProvider, DEPLOYMENT_CHOICES, Theme


class NotificationProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProvider


class MobileAppSerializer(serializers.ModelSerializer):
    deployment_mechanism = serializers.ChoiceField(choices=DEPLOYMENT_CHOICES, required=False)

    class Meta:
        model = MobileApp
        extra_kwargs = {'updated_by': {'read_only': True}}

    def _set_custom_validated_data(self, validated_data):
        """
        Here we are adding current user in 'updated_by' field
        """
        validated_data['updated_by'] = self.context['request'].user

    def create(self, validated_data):
        self._set_custom_validated_data(validated_data)
        return super(MobileAppSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        self._set_custom_validated_data(validated_data)
        return super(MobileAppSerializer, self).update(instance, validated_data)


class ThemeSerializer(serializers.ModelSerializer):
    logo_image = serializers.SerializerMethodField()

    class Meta:
        model = Theme

    def get_logo_image(self, theme):
        return get_logo_image_urls_by_organization_name(
            "{}-{}".format(theme.organization.name, theme.id),
            theme.logo_image_uploaded_at,
        )
