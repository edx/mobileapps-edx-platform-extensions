def get_api_keys(mobile_app):
    return {
        'provider_key': mobile_app.provider_key_decrypted,
        'provider_secret': mobile_app.provider_secret_decrypted,
    }


def get_provider_name(mobile_app):
    """
    this function returns notification provider name against a given mobile app
    if provider is not available it will return None
    """
    notification_provider = mobile_app.notification_provider
    if notification_provider:
        return notification_provider.name
    return notification_provider
