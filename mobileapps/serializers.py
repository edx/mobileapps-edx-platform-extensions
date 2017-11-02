from rest_framework import serializers
from mobileapps.models import MobileApp, NotificationProvider
from edx_solutions_api_integration.utils import StringCipher


class NotificationProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProvider


class MobileAppSerializer(serializers.ModelSerializer):
    provider_key = serializers.CharField(source="provider_key_decrypted", required=False)
    provider_secret = serializers.CharField(source="provider_secret_decrypted", required=False)

    class Meta:
        model = MobileApp

    def _set_provider_keys_and_user(self, validated_data):
        encrypted_provider_key = None
        encrypted_provider_secret = None

        if 'provider_key_decrypted' in validated_data:
            encrypted_provider_key = StringCipher.encrypt(validated_data.pop('provider_key_decrypted'))

        if 'provider_secret_decrypted' in validated_data:
            encrypted_provider_secret = StringCipher.encrypt(validated_data.pop('provider_secret_decrypted'))

        validated_data['provider_key'] = encrypted_provider_key
        validated_data['provider_secret'] = encrypted_provider_secret
        validated_data['updated_by'] = self.context['request'].user

    def create(self, validated_data):
        self._set_provider_keys_and_user(validated_data)
        return super(MobileAppSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        self._set_provider_keys_and_user(validated_data)
        return super(MobileAppSerializer, self).update(instance, validated_data)
