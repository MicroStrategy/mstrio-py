import unittest
from unittest.mock import patch
from mstrio.api import projects
from mstrio import microstrategy

USERNAME = "user"
PASSWORD = "password"
PROJECT_NAME = "MicroStrategy Tutorial"
BASE_URL = "https://env-xxxxx.customer.cloud.microstrategy.com/MicroStrategyLibrary/api"


class TestProjects(unittest.TestCase):

    @patch('mstrio.api.projects.requests.get')
    def test_projects(self, mock_get):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_get.return_value.status_code = 200

        response = projects.projects(conn)

        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
