import datetime
from contextlib import closing

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from edx_notifications.data import NotificationMessage
from edx_notifications.lib.publisher import get_notification_type
from edx_solutions_api_integration.permissions import (
    IsStaffOrReadOnlyView, IsStaffView, MobileAPIView, MobileListAPIView,
    MobileListCreateAPIView, MobileRetrieveUpdateAPIView,
    MobileRetrieveUpdateDestroyAPIView)
from edx_solutions_api_integration.users.serializers import SimpleUserSerializer
from edx_solutions_api_integration.utils import get_ids_from_list_param
from edx_solutions_organizations.models import Organization
from edx_solutions_organizations.serializers import BasicOrganizationSerializer
from mobileapps.image_helpers import get_image_names
from mobileapps.models import MobileApp, NotificationProvider, Theme
from mobileapps.serializers import (MobileAppSerializer,
                                    NotificationProviderSerializer,
                                    ThemeSerializer)
from mobileapps.tasks import publish_mobile_apps_notifications_task
from openedx.core.djangoapps.profile_images.exceptions import ImageValidationError
from openedx.core.djangoapps.profile_images.images import (
    IMAGE_TYPES, validate_uploaded_image)
from rest_framework import status
from rest_framework.response import Response

from .image_helpers import create_images, get_image_names, set_has_logo_image


def _save_theme_image(uploaded_image, image_sizes, name_key, image_backend):
    # validate request:
    # verify that the user's
    # ensure any file was sent
    if not uploaded_image:
        return False, "No image provided"

    # no matter what happens, delete the temporary file when we're done
    with closing(uploaded_image):
        try:
            validate_uploaded_image(uploaded_image)
        except ImageValidationError as error:
            return False, error.message

        image_names = get_image_names(settings.ORGANIZATION_THEME_IMAGE_SECRET_KEY, name_key, list(image_sizes.values()))
        create_images(uploaded_image, image_names, image_backend)
        return True, None


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
        * ios_bundle_id: ios app's bundle ID
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
        * ios_bundle_id: ios app's bundle ID
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
        * ios_bundle_id: ios app's bundle ID
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

    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

    def get_queryset(self):
        """
        Optionally restricts the returned mobile apps to a given user,
        by filtering against a 'app name' or 'organization name' query parameter in the URL.
        """
        queryset = MobileApp.objects.all()
        app_name = self.request.query_params.get('app_name', None)
        organization_name = self.request.query_params.get('organization_name', None)
        organization_ids = get_ids_from_list_param(self.request, 'organization_ids')

        if app_name is not None:
            queryset = queryset.filter(name__icontains=app_name)

        if organization_name is not None:
            queryset = queryset.filter(organizations__name__icontains=organization_name)

        if organization_ids is not None:
            queryset = queryset.filter(organizations__in=organization_ids).distinct()

        if not self.request.user.is_staff:
            user_organizations = self.request.user.organizations.all()
            queryset = queryset.filter(organizations__in=user_organizations).distinct()

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
        * ios_bundle_id: ios app's bundle ID
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
        * ios_bundle_id: ios app's bundle ID
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

    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

    def get_queryset(self):
        """
        Optionally restricts the returned mobile apps to a given user,
        by filtering against a 'app name' or 'organization name' query parameter in the URL.
        """
        queryset = MobileApp.objects.all()

        if not self.request.user.is_staff:
            user_organizations = self.request.user.organizations.all()
            queryset = queryset.filter(organizations__in=user_organizations).distinct()

        return queryset


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

    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

    def get_queryset(self):
        """
        Restricts the returned users to a given mobile app,
        by filtering against a 'mobile_app_id' in kwargs.
        """
        queryset = User.objects.filter(mobile_apps__exact=self.kwargs['mobile_app_id'])
        if not self.request.user.is_staff:
            user_organizations = self.request.user.organizations.all()
            queryset = queryset.filter(organizations__in=user_organizations)

        return queryset

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

    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

    def get_queryset(self):
        """
        Restricts the returned organizations to a given mobile app,
        by filtering against a 'mobile_app_id' in kwargs.
        """
        queryset = Organization.objects.filter(mobile_apps__exact=self.kwargs['mobile_app_id'])
        if not self.request.user.is_staff:
            queryset = queryset.filter(users=self.request.user)
        return queryset

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
    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

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
        except Exception as ex:  # pylint: disable=broad-except
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
    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

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

        except Exception as ex:  # pylint: disable=broad-except
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

    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

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

        except Exception as ex:
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
    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

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

        except Exception as ex:  # pylint: disable=broad-except
            return Response({'message':  _('Server error')}, status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': _('Accepted')}, status.HTTP_202_ACCEPTED)


def _create_notification_message(app_id, payload):
    notification_type = get_notification_type('open-edx.mobileapps.notifications')
    notification_message = NotificationMessage(
        namespace=str(app_id),
        msg_type=notification_type,
        payload=payload
    )
    return notification_message


def _make_upload_dt():
        """
        Generate a server-side timestamp for the upload. This is in a separate
        function so its behavior can be overridden in tests.
        """
        return datetime.datetime.utcnow().replace(tzinfo=utc)


class OrganizationThemeView(MobileListCreateAPIView):
    """
    **Use Case**

        Get list of themes for organization and create a new theme.

    **Example Requests**

        GET /api/server/mobileapps/organization/{id}/themes
        POST /api/server/mobileapps/organization/{id}/themes

        **POST Parameters**

        The body of the POST request must include the following parameters.

        * logo_image: Image file to be updated as a logo of the theme
        * header_bg_image: Image file to be updated as a header of the theme
        * name: Name of the theme (Optional)
        * active: theme is active or not (Optional)
        * header_background_color (Optional)
        * navigation_text_color (Optional)
        * navigation_icon_color (Optional)
        * completed_course_tint (Optional)
        * lesson_navigation_color (Optional)

    **Response Values**

        **GET**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has a paginated list of objects with the following values.

        * id: ID of the mobile app.
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * logo_image:
            - has_image
            - image_url_full
            - image_url_large
            - image_url_small
            - image_url_xsmall
            - image_url_medium
        * header_bg_image:
            - ipad_01
            - ipad_02
            - ipad_03
            - iphone_01
            - iphone_plus_01
            - mdpi
            - hdpi
            - xhdpi
            - xxhdpi
            - xxxhdpi
        * name: Name of the theme
        * active: theme is active or not
        * organization_id: organization id to which theme is related
        * header_background_color
        * navigation_text_color
        * navigation_icon_color
        * completed_course_tint
        * lesson_navigation_color

        **POST**

        If the request is successful, the request returns an HTTP 201 response.

        * id: ID of the mobile app.
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * logo_image:
            - has_image
            - image_url_full
            - image_url_large
            - image_url_small
            - image_url_xsmall
            - image_url_medium
        * header_bg_image:
            - ipad_01
            - ipad_02
            - ipad_03
            - iphone_01
            - iphone_plus_01
            - mdpi
            - hdpi
            - xhdpi
            - xxhdpi
            - xxxhdpi
        * name: Name of the theme
        * active: theme is active or not
        * organization_id: organization id to which theme is related
        * header_background_color
        * navigation_text_color
        * navigation_icon_color
        * completed_course_tint
        * lesson_navigation_color
    """

    serializer_class = ThemeSerializer

    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

    def get_queryset(self):
        """
        Optionally restricts the returned themes to active only.
        """
        queryset = Theme.objects.filter(active=True, organization_id=self.kwargs['organization_id'])
        if not self.request.user.is_staff:
            user_organizations = self.request.user.organizations.all()
            queryset = queryset.filter(organization__in=user_organizations)
        return queryset

    @transaction.atomic
    def post(self, request, organization_id):
        """
        POST method inactive the existing active theme and creates and new active one.
        """
        data = request.data.copy()
        data["organization"] = organization_id

        Theme.mark_existing_as_inactive(organization_id)
        theme_serializer = ThemeSerializer(data=data)
        if theme_serializer.is_valid(raise_exception=True):
            theme = theme_serializer.save()

            if 'logo_image' in request.FILES:
                organization = Organization.objects.get(pk=organization_id)
                uploaded_logo_image = request.FILES['logo_image']
                is_logo_saved, logo_image_response = _save_theme_image(
                    uploaded_logo_image,
                    settings.ORGANIZATION_LOGO_IMAGE_SIZES_MAP,
                    "{}-{}-{}".format(organization.name, theme.id, settings.ORGANIZATION_LOGO_IMAGE_KEY_PREFIX),
                    settings.ORGANIZATION_LOGO_IMAGE_BACKEND,
                )

                if is_logo_saved:
                    theme.logo_image_uploaded_at = _make_upload_dt()
                    theme.save(update_fields=['logo_image_uploaded_at', 'modified'])
                else:
                    return Response({"message": logo_image_response}, status=status.HTTP_400_BAD_REQUEST)

            if 'header_bg_image' in request.FILES:
                organization = Organization.objects.get(pk=organization_id)
                uploaded_header_bg_image = request.FILES['header_bg_image']
                is_header_bg_saved, header_image_response = _save_theme_image(
                    uploaded_header_bg_image,
                    settings.ORGANIZATION_HEADER_BG_IMAGE_SIZES_MAP,
                    "{}-{}-{}".format(
                        organization.name,
                        theme.id,
                        settings.ORGANIZATION_HEADER_BG_IMAGE_KEY_PREFIX,
                    ),
                    settings.ORGANIZATION_LOGO_IMAGE_BACKEND,
                )

                if is_header_bg_saved:
                    theme.header_bg_image_uploaded_at = _make_upload_dt()
                    theme.save(update_fields=['header_bg_image_uploaded_at', 'modified'])
                else:
                    return Response({"message": header_image_response}, status=status.HTTP_400_BAD_REQUEST)

            return Response(status=status.HTTP_201_CREATED)


class OrganizationThemeDetailView(MobileRetrieveUpdateDestroyAPIView):
    """
    **Use Case**

        Get theme for organization, update or destroy the existing theme.

    **Example Requests**

        GET /api/server/mobileapps/themes/{id}
        PATCH /api/server/mobileapps/themes/{id}
        PUT /api/server/mobileapps/themes/{id}
        DELETE /api/server/mobileapps//themes/{id}

        **PATCH Parameters**

        The body of the PATCH request must include the following parameters.

        * logo_image: Image file to be updated as a logo of the theme (Optional)
        * header_bg_image: Image file to be updated as a header of the theme (Optional)
        * name: Name of the theme (Optional)
        * active: theme is active or not (Optional)
        * organization_id: organization id to which theme is related
        * header_background_color
        * navigation_text_color
        * navigation_icon_color
        * completed_course_tint
        * lesson_navigation_color

        **PUT Parameters**

        The body of the PUT request must include the following parameters.

        * logo_image: Image file to be updated as a logo of the theme
        * header_bg_image: Image file to be updated as a header of the theme
        * name: Name of the theme
        * active: theme is active or not
        * organization_id: organization id to which theme is related
        * header_background_color
        * navigation_text_color
        * navigation_icon_color
        * completed_course_tint
        * lesson_navigation_color

    **Response Values**

        **GET**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has an object with the following values.

        * id: ID of the mobile app.
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * logo_image:
            - has_image
            - image_url_full
            - image_url_large
            - image_url_small
            - image_url_xsmall
            - image_url_medium
        * header_bg_image:
            - ipad_01
            - ipad_02
            - ipad_03
            - iphone_01
            - iphone_plus_01
            - mdpi
            - hdpi
            - xhdpi
            - xxhdpi
            - xxxhdpi
        * name: Name of the theme
        * active: theme is active or not
        * organization_id: organization id to which theme is related
        * header_background_color
        * navigation_text_color
        * navigation_icon_color
        * completed_course_tint
        * lesson_navigation_color

        **PATCH**

        If the request is successful, the request returns an HTTP 200 response.

        * id: ID of the mobile app.
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * logo_image:
            - has_image
            - image_url_full
            - image_url_large
            - image_url_small
            - image_url_xsmall
            - image_url_medium
        * header_bg_image:
            - ipad_01
            - ipad_02
            - ipad_03
            - iphone_01
            - iphone_plus_01
            - mdpi
            - hdpi
            - xhdpi
            - xxhdpi
            - xxxhdpi
        * name: Name of the theme
        * active: theme is active or not
        * organization_id: organization id to which theme is related
        * header_background_color
        * navigation_text_color
        * navigation_icon_color
        * completed_course_tint
        * lesson_navigation_color

        **PUT**

        If the request is successful, the request returns an HTTP 200 response.

        * id: ID of the mobile app.
        * created: Datetime it was created in.
        * modified: Datetime it was modified in.
        * logo_image:
            - has_image
            - image_url_full
            - image_url_large
            - image_url_small
            - image_url_xsmall
            - image_url_medium
        * header_bg_image:
            - ipad_01
            - ipad_02
            - ipad_03
            - iphone_01
            - iphone_plus_01
            - mdpi
            - hdpi
            - xhdpi
            - xxhdpi
            - xxxhdpi
        * name: Name of the theme
        * active: theme is active or not
        * organization_id: organization id to which theme is related
        * header_background_color
        * navigation_text_color
        * navigation_icon_color
        * completed_course_tint
        * lesson_navigation_color

        **DELETE**
        Deactivates the theme by default. Set query param `remove` to `true` to actually delete theme and its images.
    """

    serializer_class = ThemeSerializer
    lookup_url_kwarg = 'theme_id'

    def __init__(self):
        self.permission_classes += (IsStaffOrReadOnlyView,)

    def get_queryset(self):
        """
        Optionally restricts the returned themes only user's organizatons in case of non staff users.
        """
        queryset = Theme.objects.all()
        if not self.request.user.is_staff:
            user_organizations = self.request.user.organizations.all()
            queryset = queryset.filter(organization__in=user_organizations)
        return queryset

    @transaction.atomic
    def patch(self, request, theme_id):
        theme = get_object_or_404(Theme, pk=theme_id)
        theme_serializer = ThemeSerializer(theme, data=request.data)
        if theme_serializer.is_valid(raise_exception=True):
            theme = theme_serializer.save()

        if 'logo_image' in request.FILES and 'organization' in request.data:
            organization = Organization.objects.get(pk=request.data['organization'])
            uploaded_logo_image = request.FILES['logo_image']
            is_logo_saved, logo_image_response = _save_theme_image(
                uploaded_logo_image,
                settings.ORGANIZATION_LOGO_IMAGE_SIZES_MAP,
                "{}-{}-{}".format(organization.name, theme.id, settings.ORGANIZATION_LOGO_IMAGE_KEY_PREFIX),
                settings.ORGANIZATION_LOGO_IMAGE_BACKEND,
            )

            if is_logo_saved:
                theme.logo_image_uploaded_at = _make_upload_dt()
                theme.save()
            else:
                return Response({"message": logo_image_response}, status=status.HTTP_400_BAD_REQUEST)

        if 'header_bg_image' in request.FILES and 'organization' in request.data:
            organization = Organization.objects.get(pk=request.data['organization'])
            uploaded_header_bg_image = request.FILES['header_bg_image']
            is_header_bg_saved, header_image_response = _save_theme_image(
                uploaded_header_bg_image,
                settings.ORGANIZATION_HEADER_BG_IMAGE_SIZES_MAP,
                "{}-{}-{}".format(organization.name, theme.id, settings.ORGANIZATION_HEADER_BG_IMAGE_KEY_PREFIX),
                settings.ORGANIZATION_LOGO_IMAGE_BACKEND,
            )

            if is_header_bg_saved:
                theme.header_bg_image_uploaded_at = _make_upload_dt()
                theme.save()
            else:
                return Response({"message": header_image_response}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, theme_id):
        theme = get_object_or_404(Theme, pk=theme_id)
        theme_serializer = ThemeSerializer(theme, data=request.data)
        if theme_serializer.is_valid(raise_exception=True):
            theme = theme_serializer.save()

        if 'logo_image' in request.FILES and 'organization' in request.data:
            organization = Organization.objects.get(pk=request.data['organization'])
            uploaded_logo_image = request.FILES['logo_image']
            is_logo_saved, logo_image_response = _save_theme_image(
                uploaded_logo_image,
                settings.ORGANIZATION_LOGO_IMAGE_SIZES_MAP,
                "{}-{}-{}".format(organization.name, theme.id, settings.ORGANIZATION_LOGO_IMAGE_KEY_PREFIX),
                settings.ORGANIZATION_LOGO_IMAGE_BACKEND,
            )

            if is_logo_saved:
                theme.logo_image_uploaded_at = _make_upload_dt()
                theme.save(update_fields=['logo_image_uploaded_at', 'modified'])
            else:
                return Response({"message": logo_image_response}, status=status.HTTP_400_BAD_REQUEST)
        else:
            theme.remove_logo_image()

        if 'header_bg_image' in request.FILES and 'organization' in request.data:
            organization = Organization.objects.get(pk=request.data['organization'])
            uploaded_header_bg_image = request.FILES['header_bg_image']
            is_header_bg_saved, header_image_response = _save_theme_image(
                uploaded_header_bg_image,
                settings.ORGANIZATION_HEADER_BG_IMAGE_SIZES_MAP,
                "{}-{}-{}".format(organization.name, theme.id, settings.ORGANIZATION_HEADER_BG_IMAGE_KEY_PREFIX),
                settings.ORGANIZATION_LOGO_IMAGE_BACKEND,
            )

            if is_header_bg_saved:
                theme.header_bg_image_uploaded_at = _make_upload_dt()
                theme.save(update_fields=['header_bg_image_uploaded_at', 'modified'])
            else:
                return Response({"message": header_image_response}, status=status.HTTP_400_BAD_REQUEST)
        else:
            theme.remove_header_bg_image()

        return Response(status=status.HTTP_200_OK)

    def delete(self, _request, theme_id):
        remove = self.request.query_params.get('remove', False)

        theme = get_object_or_404(Theme, pk=theme_id)
        if not remove:
            theme.active = None
            theme.save(update_fields=['active', 'modified'])
        else:
            theme.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationThemeRemoveImageView(MobileRetrieveUpdateDestroyAPIView):
    """
    **Use Case**

        Remove logo image or header background image from the theme.

    **Example Requests**

        DELETE /api/server/mobileapps/themes/{id}/remove/{attribute}

        - attribute
            - Logo Image: logo_image
            - Header Background Image: header_bg_image
    """

    serializer_class = ThemeSerializer
    lookup_url_kwarg = 'theme_id'

    def __init__(self):
        self.permission_classes += (IsStaffView,)

    @transaction.atomic
    def delete(self, _request, theme_id, attribute):
        theme = get_object_or_404(Theme, pk=theme_id)

        if attribute == 'logo_image':
            theme.remove_logo_image()
        elif attribute == 'header_bg_image':
            theme.remove_header_bg_image()
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)
