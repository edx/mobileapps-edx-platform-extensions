from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.response import Response

from edx_notifications.data import NotificationMessage
from edx_notifications.lib.publisher import get_notification_type
from edx_solutions_api_integration.permissions import (
    MobileAPIView,
    MobileListAPIView,
    MobileListCreateAPIView,
    MobileRetrieveUpdateAPIView,
)
from edx_solutions_api_integration.users.serializers import SimpleUserSerializer
from edx_solutions_organizations.models import Organization
from edx_solutions_organizations.serializers import BasicOrganizationSerializer

from mobileapps.models import MobileApp, NotificationProvider
from mobileapps.serializers import MobileAppSerializer, NotificationProviderSerializer
from mobileapps.tasks import publish_mobile_apps_notifications_task


class NotificationProviderView(MobileListAPIView):
    """
    **Use Case**

        Get list of all notification providers..

    **Example Requests**

        GET /api/server/mobileapps/notification_providers

    **Response Values**

        **GET**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has a paginated list of objects with the following values.

        * id: ID of the notification provider.
        * name: Name of provider.
        * api_url: API url of the notification dashboard
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
    """
    serializer_class = NotificationProviderSerializer
    queryset = NotificationProvider.objects.all()


class MobileAppView(MobileListCreateAPIView):
    """
    **Use Case**

        Get list of mobile apps and create a new one.

    **Example Requests**

        GET /api/server/mobileapps/
        POST /api/server/mobileapps/

        **POST Parameters**

        The body of the POST request must include the following parameters.


        * name: Name of the app,
        * ios_app_id: ios app ID
        * android_app_id: Android app ID
        * ios_download_url: IOS Download URL of the app.
        * android_download_url: Android Download URL of the app.
        * deployment_mechanism: Deployment Mechanism
            1: Public app store
            2: Enterprise
            3: OTA
            4: Other
        * analytics_url: Analytics url
        * notification_provider: Notification provider selected for this app
        * provider_key: Provider key for this app
        * provider_secret: Provider secret
        * provider_dashboard_url: Provider dashboard URL
        * current_version: Current available version of the app
        * is_active: App is active or not.
        * users: List of user ids registered in the app
        * organizations: List of organization ids in this app

    **Response Values**

        **GET**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has a paginated list of objects with the following values.

        * id: ID of the mobile app.
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * name: Name of the app,
        * ios_app_id: ios app ID
        * android_app_id: Android app ID
        * ios_download_url: IOS Download URL of the app.
        * android_download_url: Android Download URL of the app.
        * deployment_mechanism: Deployment Mechanism
            1: Public app store
            2: Enterprise
            3: OTA
            4: Other
        * analytics_url: Analytics url
        * notification_provider: Notification provider selected for this app
        * provider_key: Provider key for this app
        * provider_secret: Provider secret
        * provider_dashboard_url: Provider dashboard URL
        * current_version: Current available version of the app
        * is_active: App is active or not.
        * updated_by: Record updated by the User.
        * users: List of user ids registered in the app
        * organizations: List of organization ids in this app

        **POST**

        If the request is successful, the request returns an HTTP 201 "CREATED" response.

        * id: ID of the mobile app.
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * name: Name of the app,
        * ios_app_id: ios app ID
        * android_app_id: Android app ID
        * ios_download_url: IOS Download URL of the app.
        * android_download_url: Android Download URL of the app.
        * deployment_mechanism: Deployment Mechanism
            1: Public app store
            2: Enterprise
            3: OTA
            4: Other
        * analytics_url: Analytics url
        * notification_provider: Notification provider selected for this app
        * provider_key: Provider key for this app
        * provider_secret: Provider secret
        * provider_dashboard_url: Provider dashboard URL
        * current_version: Current available version of the app
        * is_active: App is active or not.
        * updated_by: Record updated by the User.
        * users: List of user ids registered in the app
        * organizations: List of organization ids in this app
    """

    serializer_class = MobileAppSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned mobile apps to a given user,
        by filtering against a 'app name' or 'organization name' query parameter in the URL.
        """
        queryset = MobileApp.objects.all()
        app_name = self.request.query_params.get('app_name', None)
        organization_name = self.request.query_params.get('organization_name', None)

        if app_name is not None:
            queryset = queryset.filter(name__icontains=app_name)

        if organization_name is not None:
            queryset = queryset.filter(organizations__name__icontains=organization_name)

        return queryset


class MobileAppDetailView(MobileRetrieveUpdateAPIView):
    """
    **Use Case**

        Get detail of mobile app and create a new one.

    **Example Requests**

        GET /api/server/mobileapps/{id}
        PUT /api/server/mobileapps/{id}
        PATCH /api/server/mobileapps/{id}

        **PUT Parameters**

        The body of the PUT request must include the following parameters.

        * name: Name of the app,
        * ios_app_id: ios app ID
        * android_app_id: Android app ID
        * ios_download_url: IOS Download URL of the app.
        * android_download_url: Android Download URL of the app.
        * deployment_mechanism: Deployment Mechanism
            1: Public app store
            2: Enterprise
            3: OTA
            4: Other
        * analytics_url: Analytics url
        * notification_provider: Notification provider selected for this app
        * provider_key: Provider key for this app
        * provider_secret: Provider secret
        * provider_dashboard_url: Provider dashboard URL
        * current_version: Current available version of the app
        * is_active: App is active or not.
        * users: List of user ids registered in the app
        * organizations: List of organization ids in this app

    **Response Values**

        **GET/PUT/PATCH**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has a paginated list of objects with the following values.

        * id: ID of the mobile app.
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * name: Name of the app,
        * ios_app_id: ios app ID
        * android_app_id: Android app ID
        * ios_download_url: IOS Download URL of the app.
        * android_download_url: Android Download URL of the app.
        * deployment_mechanism: Deployment Mechanism
            1: Public app store
            2: Enterprise
            3: OTA
            4: Other
        * analytics_url: Analytics url
        * notification_provider: Notification provider selected for this app
        * provider_key: Provider key for this app
        * provider_secret: Provider secret
        * provider_dashboard_url: Provider dashboard URL
        * current_version: Current available version of the app
        * is_active: App is active or not.
        * updated_by: Record updated by the User.
        * users: List of user ids registered in the app
        * organizations: List of organization ids in this app
    """

    queryset = MobileApp.objects.all()
    serializer_class = MobileAppSerializer


class MobileAppUserView(MobileListAPIView):
    """
    **Use Case**

        Get users of mobile app.

    **Example Requests**

        GET /api/server/mobileapps/{id}/users
        POST /api/server/mobileapps/{id}/users
        DELETE /api/server/mobileapps/{id}/users
    """
    serializer_class = SimpleUserSerializer

    def get_queryset(self):
        """
        Restricts the returned users to a given mobile app,
        by filtering against a 'mobile_app_id' in kwargs.
        """
        return User.objects.filter(mobile_apps__exact=self.kwargs['mobile_app_id'])

    def post(self, request, mobile_app_id):
        """
        **POST Parameters**

            The body of the POST request must include the following parameters.

            * users: list of user ids to add into the mobile app

        **Response Values**

            If the request is successful, the request returns an HTTP 201 "CREATED" response.
        """
        try:
            mobileapp = MobileApp.objects.get(id=mobile_app_id)
            for user in User.objects.filter(id__in=request.data['users']):
                mobileapp.users.add(user)

            return Response({}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            raise Http404

    def delete(self, request, mobile_app_id):
        """
        **DELETE Parameters**

            The body of the DELETE request must include the following parameters.

            * users: list of user ids to remove from the mobile app

        **Response Values**

            If the request is successful, the request returns an HTTP 204 "NO CONTENT" response.
        """
        try:
            mobileapp = MobileApp.objects.get(id=mobile_app_id)
            for user in User.objects.filter(id__in=request.data['users']):
                mobileapp.users.remove(user)

            return Response({}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            raise Http404


class MobileAppOrganizationView(MobileListAPIView):
    """
    **Use Case**

        Get organizations of mobile app.

    **Example Requests**

        GET /api/server/mobileapps/{id}/organizations
        POST /api/server/mobileapps/{id}/organizations
        DELETE /api/server/mobileapps/{id}/organizations
    """
    serializer_class = BasicOrganizationSerializer

    def get_queryset(self):
        """
        Restricts the returned organizations to a given mobile app,
        by filtering against a 'mobile_app_id' in kwargs.
        """
        return Organization.objects.filter(mobile_apps__exact=self.kwargs['mobile_app_id'])

    def post(self, request, mobile_app_id):
        """
        **POST Parameters**

            The body of the POST request must include the following parameters.

            * organizations: list of organization ids to add into the mobile app

        **Response Values**

            If the request is successful, the request returns an HTTP 201 "CREATED" response.
        """
        try:
            mobileapp = MobileApp.objects.get(id=mobile_app_id)
            for organization in Organization.objects.filter(id__in=request.data['organizations']):
                mobileapp.organizations.add(organization)

            return Response({}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            raise Http404

    def delete(self, request, mobile_app_id):
        """
        **DELETE Parameters**

            The body of the DELETE request must include the following parameters.

            * organizations: list of organization ids to remove from the mobile app

        **Response Values**

            If the request is successful, the request returns an HTTP 204 "NO CONTENT" response.
        """
        try:
            mobileapp = MobileApp.objects.get(id=mobile_app_id)
            for organization in Organization.objects.filter(id__in=request.data['organizations']):
                mobileapp.organizations.remove(organization)

            return Response({}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            raise Http404


class MobileAppsNotifications(MobileAPIView):
    """
    **Use Cases**

        send a push notification to all the users of all active apps
        using app's push notifications provider.

    **Example Requests**

        POST /api/server/mobileapps/notification

        The body of the POST request must include the following parameters.

        * message: notification message

    **Response Values**

        If the request is successful, the request returns an HTTP 202 "Accepted" response.

        The HTTP 202 response has the following value.

        * message: Accepted
    """

    def post(self, request):

        message = request.data.get('message', None)
        if not message:
            return Response({'message': _('message is missing')}, status.HTTP_400_BAD_REQUEST)
        payload = {
            'title': message,
            'send_to_all': True
        }

        try:
            mobile_apps = MobileApp.objects.filter(is_active=True, notification_provider__isnull=False)
            for mobile_app in mobile_apps:
                notification_provider = mobile_app.get_notification_provider_name()
                api_keys = mobile_app.get_api_keys()
                notification_message = _create_notification_message(mobile_app.id, payload)

                # Send the notification_msg to the Celery task
                publish_mobile_apps_notifications_task.delay([], notification_message, api_keys, notification_provider)
        except Exception, ex:  # pylint: disable=broad-except
            return Response({'message':  _('Server error')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': _('Accepted')}, status.HTTP_202_ACCEPTED)


class MobileAppAllUsersNotifications(MobileAPIView):
    """
    **Use Cases**

        send a push notification to all the users of the specific app
        using app's push notifications provider.

    **Example Requests**

        POST /api/mobileapps/{id}/notification

        The body of the POST request must include the following parameters.

        * message: notification message

    **Response Values**

        If the request is successful, the request returns an HTTP 202 "Accepted" response.

        The HTTP 202 response has the following value.

        * message: Accepted
    """

    def post(self, request, mobile_app_id):

        message = request.data.get('message', None)
        if not message:
            return Response({'message': _('message is missing')}, status.HTTP_400_BAD_REQUEST)

        try:
            mobile_app = MobileApp.objects.get(pk=mobile_app_id)
            if not mobile_app.is_active:
                return Response({'message': _('Mobile app is inactive')}, status.HTTP_403_FORBIDDEN)

            notification_provider = mobile_app.get_notification_provider_name()
            if not notification_provider:
                return Response({'message': _('Notification Provider not found')}, status.HTTP_404_NOT_FOUND)
        except ObjectDoesNotExist:
            return Response({'message': _('Mobile app does not exist')}, status.HTTP_404_NOT_FOUND)

        try:
            api_keys = mobile_app.get_api_keys()
            payload = {
                'title': message,
                'send_to_all': True
            }
            notification_message = _create_notification_message(mobile_app.id, payload)

            # Send the notification_msg to the Celery task
            publish_mobile_apps_notifications_task.delay([], notification_message, api_keys, notification_provider)

        except Exception, ex:  # pylint: disable=broad-except
            return Response({'message':  _('Server error')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': _('Accepted')}, status.HTTP_202_ACCEPTED)


class MobileAppSelectedUsersNotifications(MobileAPIView):
    """
    **Use Cases**

        send a push notification to a list of given users of an app
        using app's push notifications provider.

    **Example Requests**

        POST /api/mobileapps/{id}/users/notification

        The body of the POST request must include the following parameters.

        * message: notification message
        * users: comma separated list of user ids

    **Response Values**

        If the request is successful, the request returns an HTTP 202 "Accepted" response.

        The HTTP 202 response has the following value.

        * message: Accepted
    """

    def post(self, request, mobile_app_id):

        message = request.data.get('message', None)
        if not message:
            return Response({'message': _('message is missing')}, status.HTTP_400_BAD_REQUEST)

        user_ids = request.data.get('users', None)
        if not user_ids:
            return Response({'message': _('Users list is empty')}, status.HTTP_400_BAD_REQUEST)

        try:
            mobile_app = MobileApp.objects.get(pk=mobile_app_id)
            if not mobile_app.is_active:
                return Response({'message': _('Mobile app is inactive')}, status.HTTP_403_FORBIDDEN)

            notification_provider = mobile_app.get_notification_provider_name()
            if not notification_provider:
                return Response({'message': _('Notification Provider not found')}, status.HTTP_404_NOT_FOUND)
        except ObjectDoesNotExist:
            return Response({'message': _('Mobile app does not exist')}, status.HTTP_404_NOT_FOUND)

        try:
            api_keys = mobile_app.get_api_keys()
            payload = {'title': message}
            notification_message = _create_notification_message(mobile_app.id, payload)

            # Send the notification_msg to the Celery task
            publish_mobile_apps_notifications_task.delay(user_ids, notification_message, api_keys,
                                                         notification_provider)

        except Exception, ex:
            return Response({'message':  _('Server error')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': _('Accepted')}, status.HTTP_202_ACCEPTED)


class MobileAppOrganizationAllUsersNotifications(MobileAPIView):
    """
    **Use Cases**

        send a push notification to all the users registered with the specific
        organization of the app using app's push notifications provider.

    **Example Requests**

        POST /api/mobileapps/{id}/organization/{id}/notification

        The body of the POST request must include the following parameters.

        * message: notification message

    **Response Values**

        If the request is successful, the request returns an HTTP 202 "Accepted" response.

        The HTTP 202 response has the following value.

        * message: Accepted
    """

    def post(self, request, mobile_app_id, organization_id):

        message = request.data.get('message', None)
        if not message:
            return Response({'message': _('message is missing')}, status.HTTP_400_BAD_REQUEST)

        try:
            mobile_app = MobileApp.objects.get(pk=mobile_app_id)
            if not mobile_app.is_active:
                return Response({'message': _('Mobile app is inactive')}, status.HTTP_403_FORBIDDEN)

            notification_provider = mobile_app.get_notification_provider_name()
            if not notification_provider:
                return Response({'message': _('Notification Provider not found')}, status.HTTP_404_NOT_FOUND)
        except ObjectDoesNotExist:
            return Response({'message': _('Mobile app does not exist')}, status.HTTP_404_NOT_FOUND)

        try:
            organization = mobile_app.organizations.get(id=organization_id)
            user_ids = organization.users.values_list('id', flat=True).all()
        except ObjectDoesNotExist:
            return Response({'message': _('Organization is not associated with mobile app')},
                            status.HTTP_400_BAD_REQUEST)

        try:
            api_keys = mobile_app.get_api_keys()
            payload = {'title': message}
            notification_message = _create_notification_message(mobile_app.id, payload)

            # Send the notification_msg to the Celery task
            publish_mobile_apps_notifications_task.delay(user_ids, notification_message, api_keys,
                                                         notification_provider)

        except Exception, ex:  # pylint: disable=broad-except
            return Response({'message':  _('Server error')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': _('Accepted')}, status.HTTP_202_ACCEPTED)


def _create_notification_message(app_id, payload):
    notification_type = get_notification_type(u'open-edx.mobileapps.notifications')
    notification_message = NotificationMessage(
        namespace=app_id,
        msg_type=notification_type,
        payload=payload
    )
    return notification_message
