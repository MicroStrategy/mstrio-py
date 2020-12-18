from unittest import TestCase

from mstrio.admin import dataset
from mstrio import connection
from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_dataset_admin import MockDataset


class TestDataset(TestCase):

    def setUp(self):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        dataset.objects = MockDataset.mock_objects_api()

        dataset.Dataset._API_GETTERS = {None: dataset.objects.get_object_info}
        dataset.Dataset._API_PATCH = [dataset.objects.update_object]

        self.connection = connection.Connection(base_url='http://mocked.url.com',
                                                username='username',
                                                password='password',
                                                project_name='MicroStrategy Tutorial')

    def test_init(self):
        ds = dataset.Dataset(connection=self.connection, name='My Dataset')
        self.assertIsInstance(ds, dataset.Dataset)
        self.assertEqual(ds.name, 'My Dataset')
        self.assertEqual(ds.description, 'This is My Dataset')

    def test_alter(self):
        ds = dataset.Dataset(connection=self.connection, name='My Dataset')
        ds.alter(name='My Dataset Test', description='This is My Dataset Test')
        self.assertEqual(ds.name, 'My Dataset Test')
        self.assertEqual(ds.description, 'This is My Dataset Test')

    def test_list_datasets(self):
        dss = dataset.list_datasets(connection, name='My Dataset')
        self.assertIsInstance(dss, list)
        self.assertEqual(len(dss), 1)
