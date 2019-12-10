import unittest
from unittest.mock import patch
from mstrio.api import authentication
from mstrio import microstrategy

USERNAME = "user"
PASSWORD = "password"
PROJECT_NAME = "MicroStrategy Tutorial"
BASE_URL = "https://env-xxxxx.customer.cloud.microstrategy.com/MicroStrategyLibrary/api"


class TestAuthentication(unittest.TestCase):

    def setUp(self):
        self.USERNAME = "user"
        self.PASSWORD = "password"
        self.PROJECT_NAME = "Project Name"
        self.BASE_URL = "https://acme.microstrategy.com/MicroStrategyLibrary/api"
        self.COOKIES = "test-cookie"
        self.APPCODE = 64

    @patch('mstrio.api.authentication.requests.post')
    def test_login(self, mock_post):
        conn = microstrategy.Connection(base_url=self.BASE_URL, username=self.USERNAME,
                                        password=self.PASSWORD, project_name=self.PROJECT_NAME)

        mock_post.return_value.status_code = 200

        response = authentication.login(conn)

        self.assertEqual(response.status_code, 200)

    @patch('mstrio.api.authentication.requests.post')
    def test_login_app_code_present(self, mock_post):
        """Checks that application code is present in request body."""
        conn = microstrategy.Connection(base_url=self.BASE_URL, username=self.USERNAME,
                                        password=self.PASSWORD, project_name=self.PROJECT_NAME)

        mock_post.return_value.status_code = 200
        response = authentication.login(conn)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_post.call_args[1]['data']["applicationType"], self.APPCODE)

    @patch('mstrio.api.authentication.requests.post')
    def test_login_app_code_static(self, mock_post):
        """Checks that application code is 35."""
        conn = microstrategy.Connection(base_url=self.BASE_URL, username=self.USERNAME,
                                        password=self.PASSWORD, project_name=self.PROJECT_NAME)

        mock_post.return_value.status_code = 200
        response = authentication.login(conn)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(conn.application_code, self.APPCODE)
        self.assertEqual(mock_post.call_args[1]['data']["applicationType"], self.APPCODE)

    @patch('mstrio.api.authentication.requests.post')
    def test_login_app_code_dynamic(self, mock_post):
        """Tests that changing the app code works."""
        conn = microstrategy.Connection(base_url=self.BASE_URL, username=self.USERNAME,
                                        password=self.PASSWORD, project_name=self.PROJECT_NAME)

        app_code = 99
        conn.application_code = app_code

        mock_post.return_value.status_code = 200
        response = authentication.login(conn)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(conn.application_code, app_code)
        self.assertEqual(mock_post.call_args[1]['data']["applicationType"], app_code)

    @patch('mstrio.api.authentication.requests.post')
    def test_logout(self, mock_post):
        """Validate logout method and that cookies are passed in request."""
        conn = microstrategy.Connection(base_url=self.BASE_URL, username=self.USERNAME,
                                        password=self.PASSWORD, project_name=self.PROJECT_NAME)
        conn.cookies = self.COOKIES

        mock_post.return_value.status_code = 200
        response = authentication.logout(conn)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_post.call_args[1]['cookies'], self.COOKIES)

    @patch('mstrio.api.authentication.requests.put')
    def test_sessions(self, mock_put):
        conn = microstrategy.Connection(base_url=self.BASE_URL, username=self.USERNAME,
                                        password=self.PASSWORD, project_name=self.PROJECT_NAME)

        mock_put.return_value.status_code = 200

        response = authentication.sessions(conn)

        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
