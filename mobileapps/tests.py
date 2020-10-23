# pylint: disable=E1103

"""
Run these tests @ Devstack:
paver test_system -s lms -t mobileapps
"""
import datetime
import uuid

import ddt
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.test.client import Client
from edx_notifications import startup
from edx_solutions_api_integration.test_utils import (APIClientMixin,
                                                      get_temporary_image)
from edx_solutions_organizations.models import Organization
from mobileapps.models import MobileApp, NotificationProvider, Theme
from mock import patch
from pytz import UTC
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase)

TEST_LOGO_IMAGE_UPLOAD_DT = datetime.datetime(2002, 1, 9, 15, 43, tzinfo=UTC)
TEST_HEADER_BG_IMAGE_UPLOAD_DT = datetime.datetime(2002, 1, 9, 20, 43, tzinfo=UTC)


@ddt.ddt
class NotificationProviderApiTests(ModuleStoreTestCase, APIClientMixin):
    """ Test suite for NotificationProvider API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super().setUp()
        self.base_uri = reverse('notification_providers')

        self.test_provider_name = "Test Provider Name"
        self.test_api_url = "http://example.com"

        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

    def setup_test_notification_provider(self, notification_provider_data=None):
        """
        Creates a new notification provider with given notification_provider_data
        if notification_provider_data is not present it would create notification provider with test values
        :param notification_provider_data: Dictionary witch each item represents notification provider attribute
        :return: newly created notification provider
        """
        notification_provider_data = notification_provider_data if notification_provider_data else {}
        data = {
            'name': notification_provider_data.get('name', self.test_provider_name),
            'api_url': notification_provider_data.get('api_url', self.test_api_url),

        }
        return NotificationProvider.objects.create(name=data['name'], api_url=data['api_url'])

    def test_notification_provider_list(self):
        notification_providers = []

        for i in range(30):
            data = {
                'name': 'Test Provider {}'.format(i),
                'api_url': 'http://notification/provider/{}'.format(i),
            }
            notification_providers.append(self.setup_test_notification_provider(notification_provider_data=data))

        response = self.do_get(self.base_uri)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 30)
        self.assertEqual(len(response.data['results']), 20)
        self.assertEqual(response.data['num_pages'], 2)
        for i, provider in enumerate(response.data['results']):
            self.assertEqual(provider['name'], 'Test Provider {}'.format(i))
            self.assertEqual(provider['api_url'], 'http://notification/provider/{}'.format(i))
            self.assertIsNotNone(provider['created'])
            self.assertIsNotNone(provider['modified'])

        # fetch data with page outside range
        response = self.do_get('{}?page=5'.format(self.base_uri))
        self.assertEqual(response.status_code, 404)

        # test with page_size 0, should not paginate and return all results
        response = self.do_get('{}?page_size=0'.format(self.base_uri))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(notification_providers))


@ddt.ddt
class MobileappsApiTests(ModuleStoreTestCase, APIClientMixin):
    """ Test suite for Mobileapps API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super().setUp()
        self.base_mobileapps_uri = reverse('mobileapps')

        self.test_mobileapp_name = str(uuid.uuid4())
        self.test_mobileapp_ios_app_id = str(uuid.uuid4())
        self.test_mobileapp_ios_bundle_id = str(uuid.uuid4())
        self.test_mobileapp_android_app_id = str(uuid.uuid4())
        self.test_mobileapp_deployment_mechanism = 1
        self.test_mobileapp_current_version = str(uuid.uuid4())

        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password', is_staff=True)
        self.non_staff_user = UserFactory.create(username='non_staff', email='demo@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

    def login_with_non_staff_user(self):
        self.client.logout()
        self.client.login(username=self.non_staff_user.username, password='test_password')

    def setup_test_mobileapp(self, mobileapp_data=None):
        """
        Creates a new mobileapp with given mobileapp_data
        if mobileapp_data is not present it would create mobile app with test values
        :param mobileapp_data: Dictionary witch each item represents mobile app attribute
        :return: newly created mobile app
        """
        mobileapp_data = mobileapp_data if mobileapp_data else {}
        data = {
            'name': mobileapp_data.get('name', self.test_mobileapp_name),
            'android_app_id': mobileapp_data.get('android_app_id', self.test_mobileapp_android_app_id),
            'ios_app_id': mobileapp_data.get('ios_app_id', self.test_mobileapp_ios_app_id),
            'ios_bundle_id': mobileapp_data.get('ios_bundle_id', self.test_mobileapp_ios_bundle_id),
            'current_version': mobileapp_data.get('current_version', self.test_mobileapp_current_version),
            'deployment_mechanism': mobileapp_data.get(
                'deployment_mechanism', self.test_mobileapp_deployment_mechanism),
            'provider_key': mobileapp_data.get('provider_key', 'test key'),
            'provider_secret': mobileapp_data.get('provider_secret', 'test secret'),
            'users': mobileapp_data.get('users', []),
            'organizations': mobileapp_data.get('organizations', []),
        }
        response = self.do_post(self.base_mobileapps_uri, data)
        self.assertEqual(response.status_code, 201)
        return response.data

    def test_mobileapps_list_get(self):
        mobile_apps = []
        organizations = []

        organizations.append(Organization.objects.create(name='ABC Organization'))
        organizations.append(Organization.objects.create(name='XYZ Organization'))

        users = UserFactory.create_batch(8)

        for i in range(30):
            data = {
                'name': 'Test Mobile App {}'.format(i),
                'users': [user.id for user in users],
                'organizations': [organization.id for organization in organizations],
            }
            mobile_apps.append(self.setup_test_mobileapp(mobileapp_data=data))

        response = self.do_get(self.base_mobileapps_uri)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], len(mobile_apps))
        self.assertEqual(len(response.data['results']), 20)
        self.assertEqual(response.data['num_pages'], 2)
        for i, mobileapp in enumerate(response.data['results']):
            self.assertEqual(mobileapp['name'], 'Test Mobile App {}'.format(i))
            self.assertEqual(mobileapp['updated_by'], self.user.id)
            self.assertEqual(len(mobileapp['users']), len(users))
            self.assertEqual(len(mobileapp['organizations']), len(organizations))
            self.assertIsNotNone(mobileapp['created'])
            self.assertIsNotNone(mobileapp['modified'])
            self.assertIsNotNone(mobileapp['ios_app_id'])
            self.assertIsNotNone(mobileapp['ios_bundle_id'])

        # fetch data with page outside range
        response = self.do_get('{}?page=5'.format(self.base_mobileapps_uri))
        self.assertEqual(response.status_code, 404)

        # test with page_size 0, should not paginate and return all results
        response = self.do_get('{}?page_size=0'.format(self.base_mobileapps_uri))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(mobile_apps))

    def test_mobileapps_list_by_non_staff(self):
        """
        Tests mobile apps list view with non staff user
        """
        organizations = list([
            Organization.objects.create(name='ABC Organization'),
            Organization.objects.create(name='XYZ Organization')
        ])
        for org in organizations:
            data = {
                'name': 'Test Mobile App for {}'.format(org.name),
                'organizations': [org.id],
            }
            self.setup_test_mobileapp(mobileapp_data=data)

        response = self.do_get(self.base_mobileapps_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

        organizations[0].users.add(self.non_staff_user)
        self.login_with_non_staff_user()
        response = self.do_get(self.base_mobileapps_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_mobileapps_list_search_by_app_name(self):
        mobile_apps = []

        mobile_apps.append(self.setup_test_mobileapp(mobileapp_data={"name": 'ABC App'}))
        mobile_apps.append(self.setup_test_mobileapp(mobileapp_data={"name": 'LMN App'}))
        mobile_apps.append(self.setup_test_mobileapp(mobileapp_data={"name": 'XYZ App'}))

        response = self.do_get('{}?app_name=xyz'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['num_pages'], 1)
        self.assertEqual(response.data['results'][0]['name'], "XYZ App")

        response = self.do_get('{}?app_name=app'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['num_pages'], 1)
        self.assertEqual(response.data['results'][0]['name'], "ABC App")

        response = self.do_get('{}?app_name=query'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_mobileapps_list_search_by_organization_name(self):
        mobile_apps = []
        organization1 = (Organization.objects.create(name='ABC Organization'))
        organization2 = (Organization.objects.create(name='XYZ Organization'))

        mobile_apps.append(self.setup_test_mobileapp(
            mobileapp_data={
                "name": 'ABC App', "organizations": [organization1.id, organization2.id]})
        )

        mobile_apps.append(self.setup_test_mobileapp(
            mobileapp_data={
                "name": 'XYZ App', "organizations": [organization2.id]})
        )

        response = self.do_get('{}?organization_name=xyz'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['name'], "ABC App")
        self.assertEqual(response.data['results'][1]['name'], "XYZ App")

        response = self.do_get('{}?organization_name=abc'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], "ABC App")

        response = self.do_get('{}?organization_name=query'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_mobileapps_list_search_by_organization_ids(self):
        mobile_apps = []
        organization1 = (Organization.objects.create(name='ABC Organization'))
        organization2 = (Organization.objects.create(name='XYZ Organization'))

        mobile_apps.append(self.setup_test_mobileapp(
            mobileapp_data={
                "name": 'ABC App', "organizations": [organization1.id, organization2.id]})
        )

        mobile_apps.append(self.setup_test_mobileapp(
            mobileapp_data={
                "name": 'XYZ App', "organizations": [organization2.id]})
        )

        response = self.do_get('{}?organization_ids={},{}'.format(
            self.base_mobileapps_uri,
            organization1.id,
            organization2.id,
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['organizations'], [organization1.id, organization2.id])
        self.assertEqual(response.data['results'][1]['organizations'], [organization2.id])

        response = self.do_get('{}?organization_ids={}'.format(self.base_mobileapps_uri, organization1.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['organizations'], [organization1.id, organization2.id])

        response = self.do_get('{}?organization_ids=3'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_mobileapp_post_with_non_staff_user(self):
        """
        Tests post request on mobilieapps should fail due to staff only permissions
        """
        self.login_with_non_staff_user()
        data = {
            'name': self.test_mobileapp_name,
            'android_app_id': self.test_mobileapp_android_app_id,
            'ios_app_id': self.test_mobileapp_ios_app_id,
            'current_version': self.test_mobileapp_current_version,
            'deployment_mechanism': self.test_mobileapp_deployment_mechanism,
        }
        response = self.do_post(self.base_mobileapps_uri, data)
        self.assertEqual(response.status_code, 403)

    def test_mobileapps_detail_get(self):
        mobileapp_data = self.setup_test_mobileapp(mobileapp_data={
            "name": 'ABC App', "provider_key": "ABC key",
            "provider_secret": "ABC secret", "ios_bundle_id": "com.example.testing.app"
        })

        response = self.do_get(reverse('mobileapps-detail', kwargs={'pk': mobileapp_data['id']}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'ABC App')
        self.assertEqual(response.data['updated_by'], self.user.id)
        self.assertEqual(response.data['is_active'], True)
        self.assertIn("android_app_id", response.data)
        self.assertIn("ios_app_id", response.data)
        self.assertEqual(response.data["ios_bundle_id"], "com.example.testing.app")
        self.assertIn("deployment_mechanism", response.data)
        self.assertIn("ios_download_url", response.data)
        self.assertIn("android_download_url", response.data)
        self.assertIn("analytics_url", response.data)
        self.assertIn("notification_provider", response.data)
        self.assertEqual(response.data["provider_key"], "ABC key")
        self.assertEqual(response.data["provider_secret"], "ABC secret")
        self.assertIn("provider_dashboard_url", response.data)
        self.assertIn("current_version", response.data)
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_mobileapps_detail_put(self):
        mobileapp = MobileApp.objects.create(
            name='ABC App',
            current_version=self.test_mobileapp_current_version,
            ios_app_id=self.test_mobileapp_ios_app_id,
            ios_bundle_id=self.test_mobileapp_ios_bundle_id,
            android_app_id=self.test_mobileapp_android_app_id,
            deployment_mechanism=self.test_mobileapp_deployment_mechanism,
            updated_by=self.user,
        )

        data = {
            'name': "XYZ App",
            'ios_app_id': mobileapp.ios_app_id,
            'android_app_id': mobileapp.android_app_id,
            'current_version': mobileapp.current_version,
            'deployment_mechanism': mobileapp.deployment_mechanism,
        }

        response = self.do_put(reverse('mobileapps-detail', kwargs={'pk': mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(response.data['ios_app_id'], mobileapp.ios_app_id)
        self.assertEqual(response.data['ios_bundle_id'], mobileapp.ios_bundle_id)
        self.assertEqual(response.data['android_app_id'], mobileapp.android_app_id)
        self.assertEqual(response.data['updated_by'], self.user.id)
        self.assertEqual(response.data['is_active'], mobileapp.is_active)

    def test_mobileapps_detail_patch(self):
        mobileapp = MobileApp.objects.create(
            name='ABC App',
            current_version=self.test_mobileapp_current_version,
            ios_app_id=self.test_mobileapp_ios_app_id,
            ios_bundle_id=self.test_mobileapp_ios_bundle_id,
            android_app_id=self.test_mobileapp_android_app_id,
            deployment_mechanism=self.test_mobileapp_deployment_mechanism,
            updated_by=self.user,
        )

        data = {
            'name': "XYZ App",
        }

        response = self.do_patch(reverse('mobileapps-detail', kwargs={'pk': mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(response.data['ios_app_id'], mobileapp.ios_app_id)
        self.assertEqual(response.data['ios_bundle_id'], mobileapp.ios_bundle_id)
        self.assertEqual(response.data['android_app_id'], mobileapp.android_app_id)
        self.assertEqual(response.data['updated_by'], self.user.id)
        self.assertEqual(response.data['is_active'], mobileapp.is_active)

    def test_mobileapp_put_patch_delete_with_non_staff_user(self):
        """
        Tests put/patch requests on mobilieapps detail view should fail due to staff only permissions
        """
        mobileapp = self.setup_test_mobileapp()
        self.login_with_non_staff_user()
        data = {
            'name': self.test_mobileapp_name,
            'android_app_id': self.test_mobileapp_android_app_id,
            'ios_app_id': self.test_mobileapp_ios_app_id,
            'current_version': self.test_mobileapp_current_version,
            'deployment_mechanism': self.test_mobileapp_deployment_mechanism,
        }
        response = self.do_put(reverse('mobileapps-detail', kwargs={'pk': mobileapp['id']}), data=data)
        self.assertEqual(response.status_code, 403)
        response = self.do_patch(reverse('mobileapps-detail', kwargs={'pk': mobileapp['id']}), data=data)
        self.assertEqual(response.status_code, 403)
        response = self.do_delete(reverse('mobileapps-detail', kwargs={'pk': mobileapp['id']}))
        self.assertEqual(response.status_code, 403)

    def test_mobileapp_get_with_non_staff_user(self):
        """
        Tests get requests on mobile apps detail view with non staff user
        when non staff user does not belong to the app organization
        """
        mobileapp = self.setup_test_mobileapp()
        self.login_with_non_staff_user()
        response = self.do_get(reverse('mobileapps-detail', kwargs={'pk': mobileapp['id']}))
        self.assertEqual(response.status_code, 404)

    def test_mobileapps_detail_delete(self):
        mobileapp = MobileApp.objects.create(
            name='ABC App',
            current_version=self.test_mobileapp_current_version,
            ios_app_id=self.test_mobileapp_ios_app_id,
            android_app_id=self.test_mobileapp_android_app_id,
            deployment_mechanism=self.test_mobileapp_deployment_mechanism,
            updated_by=self.user,
        )

        response = self.do_delete(reverse('mobileapps-detail', kwargs={'pk': mobileapp.id}))
        self.assertEqual(response.status_code, 405)

    def test_mobileapps_inactive(self):
        mobileapp = MobileApp.objects.create(
            name='ABC App',
            current_version=self.test_mobileapp_current_version,
            ios_app_id=self.test_mobileapp_ios_app_id,
            android_app_id=self.test_mobileapp_android_app_id,
            deployment_mechanism=self.test_mobileapp_deployment_mechanism,
            updated_by=self.user,
        )

        response = self.do_get(reverse('mobileapps-detail', kwargs={'pk': mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['is_active'], True)

        data = {
            'is_active': False
        }

        response = self.do_patch(reverse('mobileapps-detail', kwargs={'pk': mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['is_active'], False)

        response = self.do_get(self.base_mobileapps_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['is_active'], False)


@ddt.ddt
class MobileappsUserApiTests(ModuleStoreTestCase, APIClientMixin):
    """ Test suite for Mobileapps User API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super().setUp()

        self.test_mobileapp_name = str(uuid.uuid4())
        self.test_mobileapp_ios_app_id = str(uuid.uuid4())
        self.test_mobileapp_android_app_id = str(uuid.uuid4())
        self.test_mobileapp_deployment_mechanism = 1
        self.test_mobileapp_current_version = str(uuid.uuid4())
        self.users = UserFactory.create_batch(5)

        self.mobileapp = self._setup_test_mobileapp()

        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password', is_staff=True)
        self.non_staff_user = UserFactory.create(username='non_staff', email='demo@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

    def login_with_non_staff_user(self):
        self.client.logout()
        self.client.login(username=self.non_staff_user.username, password='test_password')

    def _setup_test_mobileapp(self, mobileapp_data=None, users=None):
        """
        Creates a new mobileapp with given mobileapp_data
        if mobileapp_data is not present it would create mobile app with test values
        :param
            mobileapp_data: Dictionary which each item represents mobile app attribute
            users: List of users to add in mobile app
        :return: newly created mobile app
        """
        mobileapp_data = mobileapp_data if mobileapp_data else {}
        users = users if users else self.users

        mobileapp = MobileApp.objects.create(
            name=mobileapp_data.get('name', self.test_mobileapp_name),
            ios_app_id=mobileapp_data.get('ios_app_id', self.test_mobileapp_ios_app_id),
            android_app_id=mobileapp_data.get('android_app_id', self.test_mobileapp_android_app_id),
            current_version=mobileapp_data.get('current_version', self.test_mobileapp_current_version),
            deployment_mechanism=self.test_mobileapp_deployment_mechanism,
            updated_by=self.user,
        )

        for user in users:
            mobileapp.users.add(user)
        return mobileapp

    def test_mobileapps_users(self):
        users = UserFactory.create_batch(5)

        mobileapp1 = self._setup_test_mobileapp(
            mobileapp_data={"name": "ABC App"},
            users=users[:2]
        )
        mobileapp2 = self._setup_test_mobileapp(
            mobileapp_data={"name": "XYZ App"},
            users=users[2:]
        )

        response = self.do_get(reverse('mobileapps-users', kwargs={'mobile_app_id': mobileapp1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['num_pages'], 1)

        response = self.do_get(reverse('mobileapps-users', kwargs={'mobile_app_id': mobileapp2.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['num_pages'], 1)

    def test_mobileapps_users_add(self):
        response = self.do_get(reverse('mobileapps-users', kwargs={'mobile_app_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], len(self.users))
        self.assertEqual(len(response.data['results']), len(self.users))
        self.assertEqual(response.data['num_pages'], 1)

        data = {
            "users": [user.id for user in UserFactory.create_batch(3)]
        }

        response = self.do_post(reverse('mobileapps-users', kwargs={'mobile_app_id': self.mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(reverse('mobileapps-users', kwargs={'mobile_app_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 8)
        self.assertEqual(len(response.data['results']), 8)
        self.assertEqual(response.data['num_pages'], 1)

    def test_mobileapps_users_remove(self):
        response = self.do_get(reverse('mobileapps-users', kwargs={'mobile_app_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], len(self.users))
        self.assertEqual(len(response.data['results']), len(self.users))
        self.assertEqual(response.data['num_pages'], 1)

        data = {
            "users": [user.id for user in self.users[2:]]
        }

        response = self.do_delete(reverse('mobileapps-users', kwargs={'mobile_app_id': self.mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 204)

        response = self.do_get(reverse('mobileapps-users', kwargs={'mobile_app_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['num_pages'], 1)

    def test_mobileapp_users_post_delete_with_non_staff_user(self):
        """
        Tests post/delete requests on mobilieapps users view should fail due to staff only permissions
        """
        self.login_with_non_staff_user()
        data = {
            "users": [user.id for user in UserFactory.create_batch(3)]
        }

        response = self.do_post(reverse('mobileapps-users', kwargs={'mobile_app_id': self.mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 403)
        data = {
            "users": [user.id for user in self.users[2:]]
        }

        response = self.do_delete(reverse('mobileapps-users', kwargs={'mobile_app_id': self.mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 403)

    def test_mobileapp_users_get_non_staff(self):
        """
        Tests mobile app users get for non staff user
        """
        users = UserFactory.create_batch(5)

        mobileapp1 = self._setup_test_mobileapp(
            mobileapp_data={"name": "ABC App"},
            users=users[:2]
        )
        mobileapp2 = self._setup_test_mobileapp(
            mobileapp_data={"name": "XYZ App"},
            users=users[2:]
        )
        organization = Organization.objects.create(name='XYZ Organization')
        organization.users.add(self.non_staff_user)
        for user in users[:2]:
            organization.users.add(user)
        mobileapp1.organizations.add(organization)
        self.login_with_non_staff_user()
        response = self.do_get(reverse('mobileapps-users', kwargs={'mobile_app_id': mobileapp1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

        response = self.do_get(reverse('mobileapps-users', kwargs={'mobile_app_id': mobileapp2.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)


@ddt.ddt
class MobileappsOrganizationApiTests(ModuleStoreTestCase, APIClientMixin):
    """ Test suite for Mobileapps Organization API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super().setUp()

        self.test_mobileapp_name = str(uuid.uuid4())
        self.test_mobileapp_ios_app_id = str(uuid.uuid4())
        self.test_mobileapp_android_app_id = str(uuid.uuid4())
        self.test_mobileapp_deployment_mechanism = 1
        self.test_mobileapp_current_version = str(uuid.uuid4())
        self.organizations = [
            Organization.objects.create(name='ABC Organization'),
            Organization.objects.create(name='XYZ Organization'),
        ]

        self.mobileapp = self._setup_test_mobileapp()

        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password', is_staff=True)
        self.non_staff_user = UserFactory.create(username='non_staff', email='demo@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

    def login_with_non_staff_user(self):
        self.client.logout()
        self.client.login(username=self.non_staff_user.username, password='test_password')

    def _setup_test_mobileapp(self, mobileapp_data=None, organizations=None):
        """
        Creates a new mobileapp with given mobileapp_data
        if mobileapp_data is not present it would create mobile app with test values
        :param
            mobileapp_data: Dictionary which each item represents mobile app attribute
            organizations: List of organizations to add in mobile app
        :return: newly created mobile app
        """
        mobileapp_data = mobileapp_data if mobileapp_data else {}
        organizations = organizations if organizations else self.organizations

        mobileapp = MobileApp.objects.create(
            name=mobileapp_data.get('name', self.test_mobileapp_name),
            ios_app_id=mobileapp_data.get('ios_app_id', self.test_mobileapp_ios_app_id),
            android_app_id=mobileapp_data.get('android_app_id', self.test_mobileapp_android_app_id),
            current_version=mobileapp_data.get('current_version', self.test_mobileapp_current_version),
            deployment_mechanism=self.test_mobileapp_deployment_mechanism,
            updated_by=self.user,
        )

        for organization in organizations:
            mobileapp.organizations.add(organization)
        return mobileapp

    def test_mobileapps_organizations(self):
        organization1 = Organization.objects.create(name='EFG Organization')
        organization2 = Organization.objects.create(name='LMN Organization')

        mobileapp1 = self._setup_test_mobileapp(
            mobileapp_data={"name": "ABC App"},
            organizations=[organization1]
        )
        mobileapp2 = self._setup_test_mobileapp(
            mobileapp_data={"name": "XYZ App"},
            organizations=[organization1, organization2]
        )

        response = self.do_get(reverse('mobileapps-organizations', kwargs={'mobile_app_id': mobileapp1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['num_pages'], 1)
        self.assertEqual(response.data['results'][0]['name'], organization1.name)

        response = self.do_get(reverse('mobileapps-organizations', kwargs={'mobile_app_id': mobileapp2.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['num_pages'], 1)
        self.assertEqual(response.data['results'][0]['name'], organization1.name)
        self.assertEqual(response.data['results'][1]['name'], organization2.name)

    def test_mobileapps_organizations_add(self):
        response = self.do_get(reverse('mobileapps-organizations', kwargs={'mobile_app_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], len(self.organizations))
        self.assertEqual(len(response.data['results']), len(self.organizations))
        self.assertEqual(response.data['num_pages'], 1)

        organization1 = Organization.objects.create(name='EFG Organization')
        organization2 = Organization.objects.create(name='LMN Organization')

        data = {
            "organizations": [organization1.id, organization2.id]
        }

        response = self.do_post(reverse('mobileapps-organizations',
                                        kwargs={'mobile_app_id': self.mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(reverse('mobileapps-organizations', kwargs={'mobile_app_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(len(response.data['results']), 4)
        self.assertEqual(response.data['num_pages'], 1)
        self.assertEqual(response.data['results'][0]['name'], self.organizations[0].name)
        self.assertEqual(response.data['results'][1]['name'], self.organizations[1].name)
        self.assertEqual(response.data['results'][2]['name'], organization1.name)
        self.assertEqual(response.data['results'][3]['name'], organization2.name)

    def test_mobileapps_organizations_remove(self):
        response = self.do_get(reverse('mobileapps-organizations', kwargs={'mobile_app_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], len(self.organizations))
        self.assertEqual(len(response.data['results']), len(self.organizations))
        self.assertEqual(response.data['num_pages'], 1)

        data = {
            "organizations": [self.organizations[0].id]
        }

        response = self.do_delete(reverse('mobileapps-organizations',
                                          kwargs={'mobile_app_id': self.mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 204)

        response = self.do_get(reverse('mobileapps-organizations', kwargs={'mobile_app_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['num_pages'], 1)
        self.assertEqual(response.data['results'][0]['name'], self.organizations[1].name)

    def test_mobileapp_organizations_post_delete_with_non_staff_user(self):
        """
        Tests post/delete requests on mobilieapps organizations view should fail due to staff only permissions
        """
        self.login_with_non_staff_user()
        organization = Organization.objects.create(name='Test Organization')
        data = {
            "organizations": [organization.id]
        }

        response = self.do_post(
            reverse('mobileapps-organizations', kwargs={'mobile_app_id': self.mobileapp.id}),
            data=data
        )
        self.assertEqual(response.status_code, 403)
        data = {
            "organizations": [self.organizations[0].id]
        }
        response = self.do_delete(
            reverse('mobileapps-organizations', kwargs={'mobile_app_id': self.mobileapp.id}),
            data=data
        )
        self.assertEqual(response.status_code, 403)

    def test_mobileapps_organizations_get_with_non_staff_user(self):
        """
        Tests get request on mobile apps organizations with non staff user
        """
        organization1 = Organization.objects.create(name='EFG Organization')
        organization2 = Organization.objects.create(name='LMN Organization')

        mobileapp1 = self._setup_test_mobileapp(
            mobileapp_data={"name": "ABC App"},
            organizations=[organization1]
        )
        mobileapp2 = self._setup_test_mobileapp(
            mobileapp_data={"name": "XYZ App"},
            organizations=[organization2]
        )
        organization1.users.add(self.non_staff_user)
        self.login_with_non_staff_user()
        response = self.do_get(reverse('mobileapps-organizations', kwargs={'mobile_app_id': mobileapp1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        response = self.do_get(reverse('mobileapps-organizations', kwargs={'mobile_app_id': mobileapp2.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)


@ddt.ddt
class MobileappsNotificationsTests(ModuleStoreTestCase, APIClientMixin):
    """ Test suite for Mobileapps Notifications API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_mobileapps_uri = reverse('mobileapps')

        notification_provider = NotificationProvider.objects.create(name='urban-airship')
        users = UserFactory.create_batch(5)
        organization1 = Organization.objects.create(name='ABC Organization')
        organization2 = Organization.objects.create(name='XYZ Organization')

        for user in users:
            organization1.users.add(user)

        organizations = [organization1, organization2]
        cls.organization1_id = organization1.id

        cls.user = UserFactory.create()

        app_data = {
            'name': 'ABC App',
            'notification_provider_id': notification_provider.id,
            'is_active': True
        }
        mobile_app1 = cls._setup_test_mobileapp(app_data, users, organizations)
        cls.mobile_app1_id = mobile_app1.id

        app_data = {
            'name': 'LMN App',
            'notification_provider_id': None,
            'is_active': True
        }
        mobile_app2 = cls._setup_test_mobileapp(app_data)
        cls.mobile_app2_id = mobile_app2.id

        app_data = {
            'name': 'XYZ App',
            'notification_provider_id': None,
            'is_active': False
        }
        mobile_app3 = cls._setup_test_mobileapp(app_data)
        cls.mobile_app3_id = mobile_app3.id

        users = UserFactory.create_batch(5)
        app_data = {
            'name': 'WXY App',
            'notification_provider_id': notification_provider.id,
            'is_active': True
        }
        cls._setup_test_mobileapp(app_data, users)

        startup.initialize()
        cache.clear()

    def setUp(self):
        super().setUp()

        self.non_staff_user = UserFactory.create(username='non_staff', email='demo@edx.org', password='test_password')
        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password', is_staff=True)
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

    def login_with_non_staff_user(self):
        self.client.logout()
        self.client.login(username=self.non_staff_user.username, password='test_password')

    @classmethod
    def _setup_test_mobileapp(cls, app_data, users=[], organizations=[]):
        """
        create a mobile app and associate organizations and users
        :param
            app_data: app data like name, notification_provider_id and is_active
            users: List of users to add in mobile app
            organizations: List of organization ids to add in mobile app
        :return: newly created mobile
        """

        mobile_app = MobileApp.objects.create(name="Test App",
                                              ios_app_id=str(uuid.uuid4()),
                                              android_app_id=str(uuid.uuid4()),
                                              current_version=1,
                                              provider_key='test key',
                                              provider_secret='test secret',
                                              notification_provider_id=app_data['notification_provider_id'],
                                              is_active=app_data['is_active'],
                                              updated_by=cls.user)

        for organization in organizations:
            mobile_app.organizations.add(organization)
        for user in users:
            mobile_app.users.add(user)

        return mobile_app

    @patch("edx_notifications.channels.urban_airship.UrbanAirshipNotificationChannelProvider.call_ua_push_api")
    def test_mobileapps_notifications(self, mock_ua_push_api):
        """
        send a notification to all the users of all active mobile apps
        """
        data = {'message': 'Test message to all the users of all active apps'}
        mock_ua_push_api.return_value = {'ok': 'true'}
        response = self.do_post(reverse('mobileapps-notifications'), data=data)
        self.assertEqual(response.status_code, 202)

        # test without message
        data = {'message': ''}
        response = self.do_post(reverse('mobileapps-notifications'), data=data)
        self.assertEqual(response.status_code, 400)

    @patch("edx_notifications.channels.urban_airship.UrbanAirshipNotificationChannelProvider.call_ua_push_api")
    def test_mobileapp_all_users_notifications(self, mock_ua_push_api):
        """
        send a notification to all the users of a given mobile app
        """
        data = {'message': 'Test message to all the users of an app'}
        mock_ua_push_api.return_value = {'ok': 'true'}
        response = self.do_post(
            reverse('mobileapps-all-users-notifications', kwargs={'mobile_app_id': self.mobile_app1_id}), data=data)
        self.assertEqual(response.status_code, 202)

        response = self.do_post(
            reverse('mobileapps-all-users-notifications', kwargs={'mobile_app_id': 0}), data=data)
        self.assertEqual(response.status_code, 404)

        # test without notification provider
        response = self.do_post(
            reverse('mobileapps-all-users-notifications', kwargs={'mobile_app_id': self.mobile_app2_id}), data=data)
        self.assertEqual(response.status_code, 404)

        # test inactive app
        response = self.do_post(
            reverse('mobileapps-all-users-notifications', kwargs={'mobile_app_id': self.mobile_app3_id}), data=data)
        self.assertEqual(response.status_code, 403)

        # test without message
        data = {'message': ''}
        response = self.do_post(
            reverse('mobileapps-all-users-notifications', kwargs={'mobile_app_id': self.mobile_app1_id}), data=data)
        self.assertEqual(response.status_code, 400)

    @patch("edx_notifications.channels.urban_airship.UrbanAirshipNotificationChannelProvider.call_ua_push_api")
    def test_mobileapp_selected_users_notifications(self, mock_ua_push_api):
        """
        send a notification to a list of users of a given mobile app
        """
        data = {
            'message': 'Test message to selected users of an app',
            'users': [1, 2, 4]
        }
        mock_ua_push_api.return_value = {'ok': 'true'}
        response = self.do_post(
            reverse('mobileapps-selected-users-notifications', kwargs={'mobile_app_id': self.mobile_app1_id}), data=data)

        self.assertEqual(response.status_code, 202)

        response = self.do_post(
            reverse('mobileapps-selected-users-notifications', kwargs={'mobile_app_id': 0}), data=data)
        self.assertEqual(response.status_code, 404)

        # test without notification provider
        response = self.do_post(
            reverse('mobileapps-selected-users-notifications', kwargs={'mobile_app_id': self.mobile_app2_id}), data=data)
        self.assertEqual(response.status_code, 404)

        # test inactive app
        response = self.do_post(
            reverse('mobileapps-selected-users-notifications', kwargs={'mobile_app_id': self.mobile_app3_id}), data=data)
        self.assertEqual(response.status_code, 403)

        # test without user_ids list
        data = {'message': 'Test message to selected users of an app',}
        response = self.do_post(
            reverse('mobileapps-selected-users-notifications', kwargs={'mobile_app_id': self.mobile_app1_id}), data=data)
        self.assertEqual(response.status_code, 400)

        # test without message
        data = {'message': ''}
        response = self.do_post(
            reverse('mobileapps-selected-users-notifications', kwargs={'mobile_app_id': self.mobile_app1_id}), data=data)
        self.assertEqual(response.status_code, 400)


    @patch("edx_notifications.channels.urban_airship.UrbanAirshipNotificationChannelProvider.call_ua_push_api")
    def test_mobileapp_organization_users_notifications(self, mock_ua_push_api):
        """
        send a notification to all the users of an organization associated with an app
        """
        data = {'message': 'Test message to all the users of an organization'}
        mock_ua_push_api.return_value = {'ok': 'true'}
        response = self.do_post(reverse('mobileapps-organization-all-users-notifications',
                                        kwargs={'mobile_app_id': self.mobile_app1_id,
                                                'organization_id': self.organization1_id}), data=data)

        self.assertEqual(response.status_code, 202)

        response = self.do_post(reverse('mobileapps-organization-all-users-notifications',
                                        kwargs={'mobile_app_id': 0, 'organization_id': self.organization1_id}),
                                data=data)
        self.assertEqual(response.status_code, 404)

        # test without notification provider
        response = self.do_post(reverse('mobileapps-organization-all-users-notifications',
                                        kwargs={'mobile_app_id': self.mobile_app2_id,
                                                'organization_id': self.organization1_id}), data=data)
        self.assertEqual(response.status_code, 404)

        # test inactive app
        response = self.do_post(reverse('mobileapps-organization-all-users-notifications',
                                        kwargs={'mobile_app_id': self.mobile_app3_id,
                                                'organization_id': self.organization1_id}), data=data)
        self.assertEqual(response.status_code, 403)

        # test with an invalid organization id
        response = self.do_post(reverse('mobileapps-organization-all-users-notifications',
                                        kwargs={'mobile_app_id': self.mobile_app1_id,
                                                'organization_id': 0}), data=data)
        self.assertEqual(response.status_code, 400)

        # test without message
        data = {'message': ''}
        response = self.do_post(reverse('mobileapps-organization-all-users-notifications',
                                        kwargs={'mobile_app_id': self.mobile_app1_id,
                                                'organization_id': self.organization1_id}), data=data)
        self.assertEqual(response.status_code, 400)

    def test_mobileapp_notifications_post_with_non_staff_user(self):
        """
        Tests post requests on all mobilieapps notification views by non staff users
        should fail due to staff only permissions
        """
        self.login_with_non_staff_user()
        data = {'message': 'Test message for push notification'}
        response = self.do_post(reverse('mobileapps-notifications'), data=data)
        self.assertEqual(response.status_code, 403)

        response = self.do_post(
            reverse('mobileapps-all-users-notifications', kwargs={'mobile_app_id': self.mobile_app1_id}),
            data=data
        )
        self.assertEqual(response.status_code, 403)

        response = self.do_post(
            reverse('mobileapps-selected-users-notifications', kwargs={'mobile_app_id': self.mobile_app1_id}),
            data=data
        )
        self.assertEqual(response.status_code, 403)
        response = self.do_post(
            reverse(
                'mobileapps-organization-all-users-notifications',
                kwargs={'mobile_app_id': self.mobile_app1_id, 'organization_id': self.organization1_id}
            ), data=data
        )
        self.assertEqual(response.status_code, 403)


@ddt.ddt
class MobileappsThemeApiTests(ModuleStoreTestCase, APIClientMixin):
    """ Test suite for Mobileapps Organization themes API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super().setUp()

        self.organization1 = Organization.objects.create(name='ABC Organization')
        self.organization2 = Organization.objects.create(name='XYZ Organization')

        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password', is_staff=True)
        self.non_staff_user = UserFactory.create(username='non_staff', email='demo@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

    def login_with_non_staff_user(self):
        self.client.logout()
        self.client.login(username=self.non_staff_user.username, password='test_password')

    def test_mobileapps_organization_theme(self):
        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization1.id}
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['num_pages'], 1)

        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=False,
            organization=self.organization1,
        )

        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization1.id}
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['num_pages'], 1)

        organization_theme.active = True
        organization_theme.save(update_fields=['active'])

        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization1.id}
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['num_pages'], 1)

        self.assertEqual(response.data['results'][0]['name'], 'Blue')
        self.assertIn('logo_image_uploaded_at', response.data['results'][0])
        self.assertEqual(response.data['results'][0]['organization'], self.organization1.id)
        self.assertEqual(response.data['results'][0]['logo_image']['has_image'], True)
        self.assertEqual(response.data['results'][0]['header_bg_image']['has_image'], True)

        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization2.id}
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['num_pages'], 1)

    def test_mobileapps_organization_theme_non_staff_user(self):
        """
        Tests get request on theme list view should only return theme of the organization user belongs to
        """
        self.organization1.users.add(self.non_staff_user)

        Theme.objects.create(
            name='Theme for org1',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )
        Theme.objects.create(
            name='Theme for org2',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization2,
        )
        self.login_with_non_staff_user()
        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization1.id}
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization2.id}
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_mobileapps_organization_theme_add(self):
        logo_image = get_temporary_image()
        header_bg_image = get_temporary_image()
        sample_color = '#ffffff'
        data = {
            'name': 'Test Theme',
            'active': True,
            'logo_image': logo_image,
            'header_bg_image': header_bg_image,
            'header_background_color': sample_color,
            'navigation_text_color': sample_color,
            'navigation_icon_color': sample_color,
            'completed_course_tint': sample_color,
            'lesson_navigation_color': sample_color,
        }

        response = self.do_post_multipart(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization2.id}), data,
        )

        self.assertEqual(response.status_code, 201)

        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization2.id}
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['num_pages'], 1)

        self.assertEqual(response.data['results'][0]['name'], 'Test Theme')
        self.assertIn('logo_image_uploaded_at', response.data['results'][0])
        self.assertEqual(response.data['results'][0]['organization'], self.organization2.id)

        self.assertEqual(response.data['results'][0]['header_background_color'], sample_color)
        self.assertEqual(response.data['results'][0]['navigation_text_color'], sample_color)
        self.assertEqual(response.data['results'][0]['navigation_icon_color'], sample_color)
        self.assertEqual(response.data['results'][0]['completed_course_tint'], sample_color)
        self.assertEqual(response.data['results'][0]['lesson_navigation_color'], sample_color)

        self.assertEqual(response.data['results'][0]['logo_image']['has_image'], True)
        for key, value in settings.ORGANIZATION_LOGO_IMAGE_SIZES_MAP.items():
            self.assertIn('image_url_{}'.format(key), response.data['results'][0]['logo_image'])

        self.assertEqual(response.data['results'][0]['header_bg_image']['has_image'], True)
        for key, value in settings.ORGANIZATION_HEADER_BG_IMAGE_SIZES_MAP.items():
            self.assertIn('image_url_{}'.format(key), response.data['results'][0]['header_bg_image'])

    def test_mobileapps_organization_theme_add_with_non_staff_user(self):
        self.user = UserFactory.create(username='test_non_staff', email='test@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        file_image = get_temporary_image()
        data = {
            'name': 'Test Theme',
            'active': True,
            'logo_image': file_image,
            'header_bg_image': file_image,
        }

        response = self.do_post_multipart(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization2.id}), data,
        )

        self.assertEqual(response.status_code, 403)

        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization2.id}
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)

    def test_mobileapps_organization_theme_no_file(self):
        data = {
            'name': 'Test Theme',
            'active': True,
        }

        response = self.do_post_multipart(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization2.id}), data,
        )

        self.assertEqual(response.status_code, 201)

    def test_mobileapps_organization_theme_add_and_inactive_previous(self):
        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )

        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization1.id}
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['num_pages'], 1)

        self.assertEqual(response.data['results'][0]['name'], 'Blue')
        self.assertIn('logo_image_uploaded_at', response.data['results'][0])
        self.assertEqual(response.data['results'][0]['organization'], self.organization1.id)
        self.assertEqual(response.data['results'][0]['logo_image']['has_image'], True)
        self.assertEqual(response.data['results'][0]['header_bg_image']['has_image'], True)

        file_image = get_temporary_image()
        data = {
            'name': 'Green Theme',
            'active': True,
            'logo_image': file_image,
        }

        response = self.do_post_multipart(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization1.id}), data,
        )

        self.assertEqual(response.status_code, 201)

        response = self.do_get(reverse(
            'mobileapps-organization-themes', kwargs={'organization_id': self.organization1.id}
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['num_pages'], 1)

        self.assertEqual(response.data['results'][0]['name'], 'Green Theme')
        self.assertIn('logo_image_uploaded_at', response.data['results'][0])
        self.assertEqual(response.data['results'][0]['organization'], self.organization1.id)
        self.assertEqual(response.data['results'][0]['logo_image']['has_image'], True)
        self.assertEqual(response.data['results'][0]['header_bg_image']['has_image'], False)

        # only one theme should remain active now, and it should be the latest one added
        theme = Theme.objects.get(organization_id=self.organization1.id, active=True)
        self.assertEqual(theme.active, True)
        self.assertEqual(theme.name, 'Green Theme')

        # one created before should not be active now
        theme = Theme.objects.get(id=organization_theme.id)
        self.assertEqual(theme.active, None)
        self.assertEqual(theme.name, 'Blue')

    def test_mobileapps_organization_theme_detail(self):
        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )

        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Blue')
        self.assertIn('logo_image_uploaded_at', response.data)
        self.assertEqual(response.data['organization'], self.organization1.id)
        self.assertEqual(response.data['logo_image']['has_image'], True)
        self.assertEqual(response.data['header_bg_image']['has_image'], True)

    def test_mobileapps_organization_theme_not_found(self):
        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )

        data = {
            'id': organization_theme.id,
            'name': 'Blue Theme',
            'active': True,
            'organization': self.organization1.id,
        }

        response = self.do_put(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': '1234',
            }
        ), data)
        self.assertEqual(response.status_code, 404)

        response = self.do_patch(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': '1234',
            }
        ), data)
        self.assertEqual(response.status_code, 404)

        response = self.do_put(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ), data)
        self.assertEqual(response.status_code, 200)

        response = self.do_delete(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': '1234',
            }
        ))
        self.assertEqual(response.status_code, 404)

    def test_mobileapps_organization_theme_detail_update(self):
        sample_color = '#ffffff'
        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )

        data = {
            'id': organization_theme.id,
            'name': 'Blue Theme',
            'active': True,
            'organization': self.organization1.id,
            'header_background_color': sample_color,
            'navigation_text_color': sample_color,
            'navigation_icon_color': sample_color,
            'completed_course_tint': sample_color,
            'lesson_navigation_color': sample_color,
        }

        response = self.do_patch(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ), data)

        self.assertEqual(response.status_code, 200)

        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Blue Theme')
        self.assertIn('logo_image_uploaded_at', response.data)
        self.assertEqual(response.data['organization'], self.organization1.id)
        self.assertEqual(response.data['header_background_color'], sample_color)
        self.assertEqual(response.data['navigation_text_color'], sample_color)
        self.assertEqual(response.data['navigation_icon_color'], sample_color)
        self.assertEqual(response.data['completed_course_tint'], sample_color)
        self.assertEqual(response.data['lesson_navigation_color'], sample_color)
        self.assertEqual(response.data['logo_image']['has_image'], True)
        self.assertEqual(response.data['header_bg_image']['has_image'], False)

        response = self.do_put(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ), data)

        self.assertEqual(response.status_code, 200)

        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Blue Theme')
        self.assertEqual(response.data['organization'], self.organization1.id)
        self.assertEqual(response.data['header_background_color'], sample_color)
        self.assertEqual(response.data['navigation_text_color'], sample_color)
        self.assertEqual(response.data['navigation_icon_color'], sample_color)
        self.assertEqual(response.data['completed_course_tint'], sample_color)
        self.assertEqual(response.data['lesson_navigation_color'], sample_color)
        self.assertEqual(response.data['logo_image']['has_image'], False)
        self.assertEqual(response.data['header_bg_image']['has_image'], False)

    def test_mobileapps_organization_theme_detail_update_with_non_staff_user(self):
        self.organization1.users.add(self.non_staff_user)
        self.login_with_non_staff_user()
        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )
        organization_theme2 = Theme.objects.create(
            name='Green',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization2,
        )

        data = {
            'id': organization_theme.id,
            'name': 'Blue Theme',
            'active': True,
            'organization': self.organization1.id,
        }
        response = self.do_patch(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ), data)
        self.assertEqual(response.status_code, 403)

        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Blue')
        self.assertIn('logo_image_uploaded_at', response.data)
        self.assertEqual(response.data['organization'], self.organization1.id)
        self.assertEqual(response.data['logo_image']['has_image'], True)
        self.assertEqual(response.data['header_bg_image']['has_image'], True)

        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme2.id,
            }
        ))
        self.assertEqual(response.status_code, 404)

    def test_mobileapps_organization_theme_detail_delete(self):
        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )
        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['organization'], self.organization1.id)

        response = self.do_delete(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))

        self.assertEqual(response.status_code, 204)

        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['active'], None)

    def test_mobileapps_organization_theme_detail_delete_with_non_staff_user(self):
        self.user = UserFactory.create(username='test_non_staff', email='test@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )

        response = self.do_delete(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))

        self.assertEqual(response.status_code, 403)

    def test_mobileapps_organization_theme_with_no_default_images(self):
        organization_theme = Theme.objects.create(
            name='Blue Theme',
            active=True,
            organization=self.organization1,
        )

        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Blue Theme')
        self.assertIn('logo_image_uploaded_at', response.data)
        self.assertEqual(response.data['organization'], self.organization1.id)
        self.assertEqual(response.data['logo_image']['has_image'], False)
        self.assertEqual(response.data['header_bg_image']['has_image'], False)

        for key, value in settings.ORGANIZATION_LOGO_IMAGE_SIZES_MAP.items():
            self.assertNotIn('image_url_{}'.format(key), response.data['logo_image'])

        for key, value in settings.ORGANIZATION_HEADER_BG_IMAGE_SIZES_MAP.items():
            self.assertNotIn('image_url_{}'.format(key), response.data['header_bg_image'])

    def test_mobileapps_organization_theme_remove_image(self):
        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )

        response = self.do_delete(reverse(
            'mobileapps-organization-themes-remove-image', kwargs={
                'theme_id': organization_theme.id,
                'attribute': 'logo_image'
            }
        ))
        self.assertEqual(response.status_code, 200)

        response = self.do_delete(reverse(
            'mobileapps-organization-themes-remove-image', kwargs={
                'theme_id': organization_theme.id,
                'attribute': 'header_bg_image'
            }
        ))
        self.assertEqual(response.status_code, 200)

        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['logo_image']['has_image'], False)
        self.assertEqual(response.data['header_bg_image']['has_image'], False)

    def test_mobileapps_organization_theme_remove_image_with_invalid_data(self):
        invalid_theme_id = 101
        invalid_attribute = 'logo_image_remove'
        organization_theme = Theme.objects.create(
            name='Blue',
            logo_image_uploaded_at=TEST_LOGO_IMAGE_UPLOAD_DT,
            header_bg_image_uploaded_at=TEST_HEADER_BG_IMAGE_UPLOAD_DT,
            active=True,
            organization=self.organization1,
        )

        response = self.do_delete(reverse(
            'mobileapps-organization-themes-remove-image', kwargs={
                'theme_id': invalid_theme_id,
                'attribute': 'logo_image'
            }
        ))
        self.assertEqual(response.status_code, 404)

        response = self.do_delete(reverse(
            'mobileapps-organization-themes-remove-image', kwargs={
                'theme_id': organization_theme.id,
                'attribute': invalid_attribute
            }
        ))
        self.assertEqual(response.status_code, 400)

        response = self.do_delete(reverse(
            'mobileapps-organization-themes-remove-image', kwargs={
                'theme_id': organization_theme.id,
                'attribute': 'logo_image'
            }
        ))
        self.assertEqual(response.status_code, 200)

        response = self.do_get(reverse(
            'mobileapps-organization-themes-detail', kwargs={
                'theme_id': organization_theme.id,
            }
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['logo_image']['has_image'], False)
