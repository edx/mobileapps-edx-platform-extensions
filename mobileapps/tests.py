# pylint: disable=E1103

"""
Run these tests @ Devstack:
paver test_system -s lms -t mobileapps
"""
import uuid

import ddt
from mock import patch
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test.client import Client
from edx_notifications import startup
from edx_solutions_api_integration.test_utils import (
    APIClientMixin,
)
from edx_solutions_organizations.models import Organization
from edx_solutions_api_integration.utils import StringCipher
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE
)

from mobileapps.models import MobileApp, NotificationProvider


@ddt.ddt
class NotificationProviderApiTests(ModuleStoreTestCase, APIClientMixin):
    """ Test suite for NotificationProvider API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super(NotificationProviderApiTests, self).setUp()
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

        for i in xrange(30):
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
        super(MobileappsApiTests, self).setUp()
        self.base_mobileapps_uri = reverse('mobileapps')

        self.test_mobileapp_name = str(uuid.uuid4())
        self.test_mobileapp_identifier = str(uuid.uuid4())
        self.test_mobileapp_operating_system = 1
        self.test_mobileapp_deployment_mechanism = 1
        self.test_mobileapp_current_version = str(uuid.uuid4())

        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

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
            'identifier': mobileapp_data.get('identifier', self.test_mobileapp_identifier),
            'operating_system': mobileapp_data.get('operating_system', self.test_mobileapp_operating_system),
            'current_version': mobileapp_data.get('current_version', self.test_mobileapp_current_version),
            'deployment_mechanism': mobileapp_data.get(
                'deployment_mechanism', self.test_mobileapp_deployment_mechanism),
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

        for i in xrange(30):
            data = {
                'name': 'Test Mobile App {}'.format(i),
                'identifier': 'Test Mobile App Identifier {}'.format(i),
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

        # fetch data with page outside range
        response = self.do_get('{}?page=5'.format(self.base_mobileapps_uri))
        self.assertEqual(response.status_code, 404)

        # test with page_size 0, should not paginate and return all results
        response = self.do_get('{}?page_size=0'.format(self.base_mobileapps_uri))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(mobile_apps))

    def test_mobileapps_list_search_by_app_name(self):
        mobile_apps = []

        mobile_apps.append(self.setup_test_mobileapp(mobileapp_data={"name": 'ABC App', "identifier": "ABC"}))
        mobile_apps.append(self.setup_test_mobileapp(mobileapp_data={"name": 'LMN App', "identifier": "LMN"}))
        mobile_apps.append(self.setup_test_mobileapp(mobileapp_data={"name": 'XYZ App', "identifier": "XYZ"}))

        response = self.do_get('{}?app_name=xyz'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['num_pages'], 1)
        self.assertEqual(response.data['results'][0]['name'], "XYZ App")
        self.assertEqual(response.data['results'][0]['identifier'], "XYZ")

        response = self.do_get('{}?app_name=app'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['num_pages'], 1)
        self.assertEqual(response.data['results'][0]['name'], "ABC App")
        self.assertEqual(response.data['results'][0]['identifier'], "ABC")

        response = self.do_get('{}?app_name=query'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_mobileapps_list_search_by_organization_name(self):
        mobile_apps = []
        organization1 = (Organization.objects.create(name='ABC Organization'))
        organization2 = (Organization.objects.create(name='XYZ Organization'))

        mobile_apps.append(self.setup_test_mobileapp(
            mobileapp_data={
                "name": 'ABC App', "identifier": "ABC", "organizations": [organization1.id, organization2.id]})
        )

        mobile_apps.append(self.setup_test_mobileapp(
            mobileapp_data={
                "name": 'XYZ App', "identifier": "XYZ", "organizations": [organization2.id]})
        )

        response = self.do_get('{}?organization_name=xyz'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['identifier'], "ABC")
        self.assertEqual(response.data['results'][1]['identifier'], "XYZ")

        response = self.do_get('{}?organization_name=abc'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['identifier'], "ABC")

        response = self.do_get('{}?organization_name=query'.format(self.base_mobileapps_uri))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_mobileapps_detail_get(self):
        mobileapp_data = self.setup_test_mobileapp(mobileapp_data={"name": 'ABC App', "identifier": 'ABC'})

        response = self.do_get(reverse('mobileapps-detail', kwargs={'pk': mobileapp_data['id']}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'ABC App')
        self.assertEqual(response.data['identifier'], 'ABC')
        self.assertEqual(response.data['updated_by'], self.user.id)
        self.assertEqual(response.data['is_active'], True)
        self.assertIn("operating_system", response.data)
        self.assertIn("deployment_mechanism", response.data)
        self.assertIn("download_url", response.data)
        self.assertIn("analytics_url_dev", response.data)
        self.assertIn("analytics_url_prod", response.data)
        self.assertIn("notification_provider", response.data)
        self.assertIn("provider_key", response.data)
        self.assertIn("provider_secret", response.data)
        self.assertIn("provider_dashboard_url", response.data)
        self.assertIn("current_version", response.data)
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_mobileapps_detail_put(self):
        mobileapp = MobileApp.objects.create(
            name='ABC App',
            identifier='ABC',
            current_version=self.test_mobileapp_current_version,
            operating_system=self.test_mobileapp_operating_system,
            deployment_mechanism=self.test_mobileapp_deployment_mechanism,
            updated_by=self.user,
        )

        data = {
            'name': "XYZ App",
            'identifier': mobileapp.identifier,
            'current_version': mobileapp.current_version,
            'operating_system': mobileapp.operating_system,
        }

        response = self.do_put(reverse('mobileapps-detail', kwargs={'pk': mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(response.data['identifier'], mobileapp.identifier)
        self.assertEqual(response.data['updated_by'], self.user.id)
        self.assertEqual(response.data['is_active'], mobileapp.is_active)

    def test_mobileapps_detail_patch(self):
        mobileapp = MobileApp.objects.create(
            name='ABC App',
            identifier='ABC',
            operating_system=self.test_mobileapp_operating_system,
            current_version=self.test_mobileapp_current_version,
            deployment_mechanism=self.test_mobileapp_deployment_mechanism,
            updated_by=self.user
        )

        data = {
            'name': "XYZ App",
        }

        response = self.do_patch(reverse('mobileapps-detail', kwargs={'pk': mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(response.data['identifier'], mobileapp.identifier)
        self.assertEqual(response.data['updated_by'], self.user.id)
        self.assertEqual(response.data['is_active'], mobileapp.is_active)

    def test_mobileapps_detail_delete(self):
        mobileapp = MobileApp.objects.create(
            name='ABC App',
            identifier='ABC',
            operating_system=self.test_mobileapp_operating_system,
            current_version=self.test_mobileapp_current_version,
            deployment_mechanism=self.test_mobileapp_deployment_mechanism,
            updated_by=self.user
        )

        response = self.do_delete(reverse('mobileapps-detail', kwargs={'pk': mobileapp.id}))
        self.assertEqual(response.status_code, 405)

    def test_mobileapps_inactive(self):
        mobileapp = MobileApp.objects.create(
            name='ABC App',
            identifier='ABC',
            operating_system=self.test_mobileapp_operating_system,
            current_version=self.test_mobileapp_current_version,
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
        super(MobileappsUserApiTests, self).setUp()

        self.test_mobileapp_name = str(uuid.uuid4())
        self.test_mobileapp_identifier = str(uuid.uuid4())
        self.test_mobileapp_operating_system = 1
        self.test_mobileapp_deployment_mechanism = 1
        self.test_mobileapp_current_version = str(uuid.uuid4())
        self.users = UserFactory.create_batch(5)

        self.mobileapp = self._setup_test_mobileapp()

        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

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
            identifier=mobileapp_data.get('identifier', self.test_mobileapp_identifier),
            operating_system=mobileapp_data.get('operating_system', self.test_mobileapp_operating_system),
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
            mobileapp_data={"name": "ABC App", "identifier": "ABC"},
            users=users[:2]
        )
        mobileapp2 = self._setup_test_mobileapp(
            mobileapp_data={"name": "XYZ App", "identifier": "XYZ"},
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


@ddt.ddt
class MobileappsOrganizationApiTests(ModuleStoreTestCase, APIClientMixin):
    """ Test suite for Mobileapps Organization API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super(MobileappsOrganizationApiTests, self).setUp()

        self.test_mobileapp_name = str(uuid.uuid4())
        self.test_mobileapp_identifier = str(uuid.uuid4())
        self.test_mobileapp_operating_system = 1
        self.test_mobileapp_deployment_mechanism = 1
        self.test_mobileapp_current_version = str(uuid.uuid4())
        self.organizations = [
            Organization.objects.create(name='ABC Organization'),
            Organization.objects.create(name='XYZ Organization'),
        ]

        self.mobileapp = self._setup_test_mobileapp()

        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

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
            identifier=mobileapp_data.get('identifier', self.test_mobileapp_identifier),
            operating_system=mobileapp_data.get('operating_system', self.test_mobileapp_operating_system),
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
            mobileapp_data={"name": "ABC App", "identifier": "ABC"},
            organizations=[organization1]
        )
        mobileapp2 = self._setup_test_mobileapp(
            mobileapp_data={"name": "XYZ App", "identifier": "XYZ"},
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


@ddt.ddt
class MobileappsNotificationsTests(ModuleStoreTestCase, APIClientMixin):
    """ Test suite for Mobileapps Notifications API views """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(MobileappsNotificationsTests, cls).setUpClass()
        cls.base_mobileapps_uri = reverse('mobileapps')

        notification_provider = NotificationProvider.objects.create(name='urban-airship')
        users = UserFactory.create_batch(5)
        organization1 = Organization.objects.create(name='ABC Organization')
        organization2 = Organization.objects.create(name='XYZ Organization')

        for user in users:
            organization1.users.add(user)

        organizations = [organization1, organization2]

        cls.organization1_id = organization1.id

        app_data = {
            'identifier': 'ABC identifier',
            'notification_provider_id': notification_provider.id,
            'is_active': True
        }
        mobile_app1 = cls._setup_test_mobileapp(app_data, users, organizations)
        cls.mobile_app1_id = mobile_app1.id

        app_data = {
            'identifier': 'LMN identifier',
            'notification_provider_id': None,
            'is_active': True
        }
        mobile_app2 = cls._setup_test_mobileapp(app_data)
        cls.mobile_app2_id = mobile_app2.id

        app_data = {
            'identifier': 'XYZ identifier',
            'notification_provider_id': None,
            'is_active': False
        }
        mobile_app3 = cls._setup_test_mobileapp(app_data)
        cls.mobile_app3_id = mobile_app3.id

        startup.initialize()
        cache.clear()

    def setUp(self):
        super(MobileappsNotificationsTests, self).setUp()

        self.user = UserFactory.create(username='test', email='test@edx.org', password='test_password')
        self.client = Client()
        self.client.login(username=self.user.username, password='test_password')

        cache.clear()

    @classmethod
    def _setup_test_mobileapp(cls, app_data, users=[], organizations=[]):
        """
        create a mobile app and associate organizations and users
        :param
            app_data: app data like identifier, notification_provider_id and is_active
            users: List of users to add in mobile app
            organizations: List of organization ids to add in mobile app
        :return: newly created mobile
        """

        mobile_app = MobileApp.objects.create(name="Test App",
                                              identifier=app_data['identifier'],
                                              operating_system=1,
                                              current_version=1,
                                              provider_key=StringCipher.encrypt('test key'),
                                              provider_secret=StringCipher.encrypt('test secret'),
                                              notification_provider_id=app_data['notification_provider_id'],
                                              is_active=app_data['is_active'],
                                              updated_by=cls.user)

        for organization in organizations:
            mobile_app.organizations.add(organization)
        for user in users:
            mobile_app.users.add(user)

        return mobile_app

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
