"""
This file contains celery tasks for sending push notifications
"""
import logging

from celery.task import task  # pylint: disable=no-name-in-module, import-error
from edx_notifications.lib.publisher import bulk_publish_notification_to_users

log = logging.getLogger('edx.celery.task')


@task()
def publish_mobile_apps_notifications_task(user_ids, notification_msg, api_keys, provider):
    """
    This function will call the edx_notifications api method "bulk_publish_notification_to_users"
    and run as a new Celery task.
    """
    try:
        bulk_publish_notification_to_users(user_ids, notification_msg, preferred_channel=provider,
                                           channel_context={"api_credentials": api_keys})
    except Exception as ex:
        # Notifications are never critical, so we don't want to disrupt any
        # other logic processing. So log and continue.
        log.exception(ex)
