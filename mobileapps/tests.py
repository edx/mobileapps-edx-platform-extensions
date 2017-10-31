# pylint: disable=E1103

"""
Run these tests @ Devstack:
paver test_system -s lms -t mobileapps
"""
import uuid
import ddt
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory, Client

from mobileapps.models import MobileApp
from student.tests.factories import CourseEnrollmentFactory, UserFactory, GroupFactory
from edx_solutions_organizations.models import Organization
from django.core.cache import cache
from edx_solutions_api_integration.test_utils import (
    APIClientMixin,
)
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE
)


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
        self.test_mobileapp_current_version = str(uuid.uuid4())

        self.user = UserFactory.build(username='test', email='test@edx.org', password='test_password')
        self.user.save()
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
                'current_version': '1.0',
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
        self.test_mobileapp_current_version = str(uuid.uuid4())
        self.users = UserFactory.create_batch(5)

        self.mobileapp = self._setup_test_mobileapp()

        self.user = UserFactory.build(username='test', email='test@edx.org', password='test_password')
        self.user.save()
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

        response = self.do_get(reverse('mobileapps-users', kwargs={'mobileapp_id': mobileapp1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['num_pages'], 1)

        response = self.do_get(reverse('mobileapps-users', kwargs={'mobileapp_id': mobileapp2.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['num_pages'], 1)

    def test_mobileapps_users_add(self):
        response = self.do_get(reverse('mobileapps-users', kwargs={'mobileapp_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], len(self.users))
        self.assertEqual(len(response.data['results']), len(self.users))
        self.assertEqual(response.data['num_pages'], 1)

        data = {
            "users": [user.id for user in UserFactory.create_batch(3)]
        }

        response = self.do_post(reverse('mobileapps-users', kwargs={'mobileapp_id': self.mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(reverse('mobileapps-users', kwargs={'mobileapp_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 8)
        self.assertEqual(len(response.data['results']), 8)
        self.assertEqual(response.data['num_pages'], 1)

    def test_mobileapps_users_remove(self):
        response = self.do_get(reverse('mobileapps-users', kwargs={'mobileapp_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], len(self.users))
        self.assertEqual(len(response.data['results']), len(self.users))
        self.assertEqual(response.data['num_pages'], 1)

        data = {
            "users": [user.id for user in self.users[2:]]
        }

        response = self.do_delete(reverse('mobileapps-users', kwargs={'mobileapp_id': self.mobileapp.id}), data=data)
        self.assertEqual(response.status_code, 204)

        response = self.do_get(reverse('mobileapps-users', kwargs={'mobileapp_id': self.mobileapp.id}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['num_pages'], 1)
