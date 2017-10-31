from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from rest_framework.response import Response
from rest_framework import status

from mobileapps.models import MobileApp
from mobileapps.serializers import MobileAppSerializer
from edx_solutions_api_integration.permissions import (
    SecureListCreateAPIView,
    SecureRetrieveUpdateAPIView,
    SecureListAPIView,
)
from edx_solutions_api_integration.users.serializers import SimpleUserSerializer
from edx_solutions_organizations.models import Organization
from edx_solutions_organizations.serializers import BasicOrganizationSerializer


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

