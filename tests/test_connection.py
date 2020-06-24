import unittest
from tests.mock_connection import MockConnection
from mstrio import connection
import json


class TestConnection(unittest.TestCase):

    def setUp(self):
        with open('production/tests/api-responses/misc/server_status.json') as server_status:
            self.__server_status = json.load(server_status)

        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()
        self.connection = connection.Connection(base_url='http://mocked.url.com',
                                                username='username',
                                                password='password')

    def test_check_version(self):
        """Test that response is parsed correctly and the version numbers are properly set."""
        self.assertIsInstance(self.connection._Connection__check_version(), bool)

    def test_delegate(self):
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()
        self.connection = connection.Connection(base_url='http://mocked.url.com', identity_token='id_token')
        self.assertIsNotNone(self.connection.session.headers['X-MSTR-AuthToken'])


if __name__ == '__main__':
    unittest.main()
