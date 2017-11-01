from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.response import Response

from edx_notifications.data import NotificationMessage
from edx_notifications.lib.publisher import get_notification_type
from edx_solutions_api_integration.permissions import (
    SecureListCreateAPIView,
    SecureRetrieveUpdateAPIView,
    SecureListAPIView,
    SecureAPIView,
)
from edx_solutions_api_integration.users.serializers import SimpleUserSerializer
from edx_solutions_organizations.models import Organization
from edx_solutions_organizations.serializers import BasicOrganizationSerializer


from mobileapps.models import MobileApp
from mobileapps.serializers import MobileAppSerializer
from mobileapps.tasks import publish_mobile_apps_notifications_task


class MobileAppView(SecureListCreateAPIView):
    """
    **Use Case**

        Get list of mobile apps and create a new one.

    **Example Requests**

        GET /api/server/mobileapps/
        POST /api/server/mobileapps/

        **POST Parameters**

        The body of the POST request must include the following parameters.

        * identifier: Unique Identifier of the app.
        * name: Name of the app,
        * operating_system: OS version
            1: Android
            2: iOS
            3: Windows
            4: Other
        * download_url: Download URL of the app.
        * analytics_url_dev: Analytics url for development environment
        * analytics_url_prod: Analytics url for Production
        * ua_key: Urban airship key for this app
        * ua_secret: Urban airship secret
        * ua_dashboard_url: Urban airship dashboard URL
        * current_version: Current available version of the app
        * is_active: App is active or not.
        * users: List of user ids registered in the app
        * organizations: List of organization ids uses this app

    **Response Values**

        **GET**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has a paginated list of objects with the following values.

        * id: ID of the mobile app.,
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * identifier: Unique Identifier of the app.
        * name: Name of the app,
        * operating_system: OS version
            1: Android
            2: iOS
            3: Windows
            4: Other
        * download_url: Download URL of the app.
        * analytics_url_dev: Analytics url for development environment
        * analytics_url_prod: Analytics url for Production
        * ua_key: Urban airship key for this app
        * ua_secret: Urban airship secret
        * ua_dashboard_url: Urban airship dashboard URL
        * current_version: Current available version of the app
        * is_active: App is active or not.
        * updated_by: Record updated by the User.
        * users: Users registered in the app
        * organizations: Organizations uses this app
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


class MobileAppDetailView(SecureRetrieveUpdateAPIView):
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
        * operating_system: OS version
            1: Android
            2: iOS
            3: Windows
            4: Other
        * download_url: Download URL of the app.
        * analytics_url_dev: Analytics url for development environment
        * analytics_url_prod: Analytics url for Production
        * ua_key: Urban airship key for this app
        * ua_secret: Urban airship secret
        * ua_dashboard_url: Urban airship dashboard URL
        * current_version: Current available version of the app
        * is_active: App is active or not.
        * users: List of user ids registered in the app
        * organizations: List of organization ids uses this app

    **Response Values**

        **GET/PUT/PATCH**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has a paginated list of objects with the following values.

        * id: ID of the mobile app.,
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * identifier: Unique Identifier of the app.
        * name: Name of the app,
        * operating_system: OS version
            1: Android
            2: iOS
            3: Windows
            4: Other
        * download_url: Download URL of the app.
        * analytics_url_dev: Analytics url for development environment
        * analytics_url_prod: Analytics url for Production
        * ua_key: Urban airship key for this app
        * ua_secret: Urban airship secret
        * ua_dashboard_url: Urban airship dashboard URL
        * current_version: Current available version of the app
        * is_active: App is active or not.
        * updated_by: Record updated by the User.
        * users: Users registered in the app
        * organizations: Organizations uses this app
    """

    queryset = MobileApp.objects.all()
    serializer_class = MobileAppSerializer


class MobileAppUserView(SecureListAPIView):
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
        by filtering against a 'mobileapp_id' in kwargs.
        """
        return User.objects.filter(mobile_apps__exact=self.kwargs['mobileapp_id'])

    def post(self, request, mobileapp_id):
        """
        **POST Parameters**

            The body of the POST request must include the following parameters.

            * users: list of user ids to add into the mobile app

        **Response Values**

            If the request is successful, the request returns an HTTP 201 "CREATED" response.
        """
        try:
            mobileapp = MobileApp.objects.get(id=mobileapp_id)
            for user in User.objects.filter(id__in=request.data['users']):
                mobileapp.users.add(user)

            return Response({}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            raise Http404

    def delete(self, request, mobileapp_id):
        """
        **DELETE Parameters**

            The body of the DELETE request must include the following parameters.

            * users: list of user ids to remove from the mobile app

        **Response Values**

            If the request is successful, the request returns an HTTP 204 "NO CONTENT" response.
        """
        try:
            mobileapp = MobileApp.objects.get(id=mobileapp_id)
            for user in User.objects.filter(id__in=request.data['users']):
                mobileapp.users.remove(user)

            return Response({}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            raise Http404


class MobileAppOrganizationView(SecureListAPIView):
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
        by filtering against a 'mobileapp_id' in kwargs.
        """
        return Organization.objects.filter(mobile_apps__exact=self.kwargs['mobileapp_id'])

    def post(self, request, mobileapp_id):
        """
        **POST Parameters**

            The body of the POST request must include the following parameters.

            * organizations: list of organization ids to add into the mobile app

        **Response Values**

            If the request is successful, the request returns an HTTP 201 "CREATED" response.
        """
        try:
            mobileapp = MobileApp.objects.get(id=mobileapp_id)
            for organization in Organization.objects.filter(id__in=request.data['organizations']):
                mobileapp.organizations.add(organization)

            return Response({}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            raise Http404

    def delete(self, request, mobileapp_id):
        """
        **DELETE Parameters**

            The body of the DELETE request must include the following parameters.

            * organizations: list of organization ids to remove from the mobile app

        **Response Values**

            If the request is successful, the request returns an HTTP 204 "NO CONTENT" response.
        """
        try:
            mobileapp = MobileApp.objects.get(id=mobileapp_id)
            for organization in Organization.objects.filter(id__in=request.data['organizations']):
                mobileapp.organizations.remove(organization)

            return Response({}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            raise Http404


class MobileAppAllUsersNotifications(SecureAPIView):
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

    def post(self, request, pk):

        message = request.data.get('message', None)
        if not message:
            return Response({'message': _('message is missing')}, status.HTTP_400_BAD_REQUEST)

        try:
            mobile_app = MobileApp.objects.get(pk=pk)
            if not mobile_app.is_active:
                return Response({'message': _('Mobile app is inactive')}, status.HTTP_403_FORBIDDEN)
        except ObjectDoesNotExist:
            return Response({'message': _('Mobile app does not exist')}, status.HTTP_404_NOT_FOUND)

        try:
            api_keys = mobile_app.get_api_keys()
            notification_provider = mobile_app.get_notifications_provider()
            if not notification_provider:
                return Response({'message': _('Notification Provider not found')}, status.HTTP_404_NOT_FOUND)
            notification_message = _create_notification_message(message, mobile_app.identifier, send_to_all=True)

            # Send the notification_msg to the Celery task
            publish_mobile_apps_notifications_task.delay([], notification_message, api_keys, notification_provider)

        except Exception, ex:  # pylint: disable=broad-except
            return Response({'message':  _('Server error')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': _('Accepted')}, status.HTTP_202_ACCEPTED)


class MobileAppSelectedUsersNotifications(SecureAPIView):
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

    def post(self, request, pk):

        message = request.data.get('message', None)
        if not message:
            return Response({'message': _('message is missing')}, status.HTTP_400_BAD_REQUEST)

        user_ids = request.data.get('users', None)
        if not user_ids:
            return Response({'message': _('Users list is empty')}, status.HTTP_400_BAD_REQUEST)

        try:
            mobile_app = MobileApp.objects.get(pk=pk)
            if not mobile_app.is_active:
                return Response({'message': _('Mobile app is inactive')}, status.HTTP_403_FORBIDDEN)
        except ObjectDoesNotExist:
            return Response({'message': _('Mobile app does not exist')}, status.HTTP_404_NOT_FOUND)

        try:
            api_keys = mobile_app.get_api_keys()
            notification_provider = mobile_app.get_notifications_provider()
            if not notification_provider:
                return Response({'message': _('Notification Provider not found')}, status.HTTP_404_NOT_FOUND)
            notification_message = _create_notification_message(message, mobile_app.identifier)

            # Send the notification_msg to the Celery task
            publish_mobile_apps_notifications_task.delay(user_ids, notification_message, api_keys,
                                                         notification_provider)

        except Exception, ex:
            return Response({'message':  _('Server error')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': _('Accepted')}, status.HTTP_202_ACCEPTED)


class MobileAppOrganizationAllUsersNotifications(SecureAPIView):
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

    def post(self, request, pk, organization_id):

        message = request.data.get('message', None)
        if not message:
            return Response({'message': _('message is missing')}, status.HTTP_400_BAD_REQUEST)

        try:
            mobile_app = MobileApp.objects.get(pk=pk)
            if not mobile_app.is_active:
                return Response({'message': _('Mobile app is inactive')}, status.HTTP_403_FORBIDDEN)
        except ObjectDoesNotExist:
            return Response({'message': _('Mobile app does not exist')}, status.HTTP_404_NOT_FOUND)

        try:
            organization = mobile_app.organizations.get(id=organization_id)
        except ObjectDoesNotExist:
            return Response({'message': _('Organization is not associated with mobile app')},
                            status.HTTP_400_BAD_REQUEST)
        try:
            user_ids = organization.users.values_list('id', flat=True).all()
            api_keys = mobile_app.get_api_keys()
            notification_provider = mobile_app.get_notifications_provider()
            if not notification_provider:
                return Response({'message': _('Notification Provider not found')}, status.HTTP_404_NOT_FOUND)
            notification_message = _create_notification_message(message, mobile_app.identifier)

            # Send the notification_msg to the Celery task
            publish_mobile_apps_notifications_task.delay(user_ids, notification_message, api_keys,
                                                         notification_provider)

        except Exception, ex:  # pylint: disable=broad-except
            return Response({'message':  _('Server error')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': _('Accepted')}, status.HTTP_202_ACCEPTED)


def _create_notification_message(title, app_identifier, send_to_all=False):
    notification_type = get_notification_type(u'open-edx.mobileapps.notifications')
    notification_message = NotificationMessage(
        namespace=app_identifier,
        msg_type=notification_type,
        payload={
            'title': title,
            'send_to_all': send_to_all
        }
    )
    return notification_message
