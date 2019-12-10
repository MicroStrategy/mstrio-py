import unittest
from unittest.mock import Mock, patch
from mstrio.microstrategy import Connection
import json
from nose.tools import assert_true

class TestMicrostrategy(unittest.TestCase):

    @patch('mstrio.api.projects.projects', autospec=True)
    @patch('mstrio.api.authentication.login', autospec=True)
    def setUp(self, mock_login, mock_projects):
        with open('production/tests/api-responses/misc/server_status.json') as server_status:
            self.__server_status =json.load(server_status)
        self.username = 'user'
        self.password = 'pass'
        self.base_url = 'https://test-env.customer.cloud.microstrategy.com/MicroStrategyLibrary/api/'
        self.project_id = 'B7CA92F04B9FAE8D941C3E9B7E0CD754'
        self.__web_version = '11.1.0400'
        self.__iserver_version = '11.1.0400'

        mock_login.return_value.ok = True
        mock_projects.return_value.ok = True
        self.conn = Connection(self.base_url, self.username, self.password,
                          self.project_id)

    @patch('mstrio.api.misc.server_status', autospec=True)
    def test_check_version(self, mock_server_status):
        """Test that response is parsed correctly and the version numbers are properly set."""
        # Configure the mock to return a response with an OK status code.
        mock_server_status.return_value.ok = True

        # mock the response from misc.server_status()
        mock_server_status.return_value = Mock(ok=True)
        mock_server_status.return_value.json.return_value = self.__server_status

        self.assertIsInstance(self.conn._Connection__check_version(), bool)
        assert_true(mock_server_status.called)
        self.assertEqual(self.conn._Connection__web_version, self.__web_version)
        self.assertEqual(self.conn._Connection__iserver_version,
                         self.__iserver_version)


if __name__ == '__main__':
    unittest.main()
