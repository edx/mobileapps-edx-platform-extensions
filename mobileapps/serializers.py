from rest_framework import serializers
from mobileapps.models import MobileApp, NotificationProvider, DEPLOYMENT_CHOICES


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
