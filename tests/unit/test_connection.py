import unittest
from production.tests.resources.mocks.mock_connection import MockConnection
from mstrio import connection
import json


class TestConnection(unittest.TestCase):

    def setUp(self):
        with open('production/tests/resources/api-responses/misc/server_status.json') as server_status:
            self.__server_status = json.load(server_status)

        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()
        self.connection = connection.Connection(base_url='http://mocked.url.com',
                                                username='username',
                                                password='password')

    def test_check_version(self):
        """Test that response is parsed correctly and the version numbers are
        properly set."""
        self.assertIsInstance(self.connection._Connection__check_version(), bool)

    def test_delegate(self):
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()
        self.connection = connection.Connection(base_url='http://mocked.url.com', identity_token='id_token')
        self.assertIsNotNone(self.connection.session.headers['X-MSTR-AuthToken'])

    def test_select_connection(self):
        self.assertIsNone(self.connection.project_id)
        self.assertIsNone(self.connection.project_name)

        self.connection.select_project(project_id='CE52831411E696C8BD2F0080EFD5AF44')
        self.assertEquals(self.connection.project_id, 'CE52831411E696C8BD2F0080EFD5AF44')
        self.assertEquals(self.connection.project_name, 'Consolidated Education Project')

        self.connection.select_project(project_name='MicroStrategy Tutorial')
        self.assertEquals(self.connection.project_id, 'B7CA92F04B9FAE8D941C3E9B7E0CD754')
        self.assertEquals(self.connection.project_name, 'MicroStrategy Tutorial')

        self.connection.select_project(project_id='CE52831411E696C8BD2F0080EFD5AF44',
                                       project_name='MicroStrategy Tutorial')
        self.assertEquals(self.connection.project_id, 'CE52831411E696C8BD2F0080EFD5AF44')
        self.assertEquals(self.connection.project_name, 'Consolidated Education Project')

        self.connection.select_project()
        self.assertIsNone(self.connection.project_id)
        self.assertIsNone(self.connection.project_name)

if __name__ == '__main__':
    unittest.main()
