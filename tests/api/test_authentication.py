import unittest
from unittest.mock import patch
from mstrio.api import authentication
from mstrio import microstrategy

USERNAME = "user"
PASSWORD = "password"
PROJECT_NAME = "MicroStrategy Tutorial"
BASE_URL = "https://env-xxxxx.customer.cloud.microstrategy.com/MicroStrategyLibrary/api"


class TestAuthentication(unittest.TestCase):

    @patch('mstrio.api.authentication.requests.post')
    def test_login(self, mock_post):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_post.return_value.status_code = 200

        response = authentication.login(conn)

        self.assertEqual(response.status_code, 200)

    @patch('mstrio.api.authentication.requests.post')
    def test_logout(self, mock_post):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_post.return_value.status_code = 200

        response = authentication.logout(conn)

        self.assertEqual(response.status_code, 200)

    @patch('mstrio.api.authentication.requests.put')
    def test_sessions(self, mock_put):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_put.return_value.status_code = 200

        response = authentication.sessions(conn)

        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
