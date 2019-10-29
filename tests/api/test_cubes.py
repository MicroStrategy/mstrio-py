import unittest
from unittest.mock import patch
from mstrio.api import cubes
from mstrio import microstrategy

USERNAME = "user"
PASSWORD = "password"
PROJECT_NAME = "MicroStrategy Tutorial"
BASE_URL = "https://env-xxxxx.customer.cloud.microstrategy.com/MicroStrategyLibrary/api"
CUBE_ID = "1"
INSTANCE_ID = "2"


class TestCubes(unittest.TestCase):

    @patch('mstrio.api.cubes.requests.get')
    def test_cube(self, mock_get):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_get.return_value.status_code = 200

        response = cubes.cube(conn, cube_id=CUBE_ID)

        self.assertEqual(response.status_code, 200)

    @patch('mstrio.api.cubes.requests.post')
    def test_cube_instance(self, mock_post):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_post.return_value.status_code = 200

        response = cubes.cube_instance(conn, cube_id=CUBE_ID)

        self.assertEqual(response.status_code, 200)

    @patch('mstrio.api.cubes.requests.get')
    def test_cube_instance_id(self, mock_get):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_get.return_value.status_code = 200

        response = cubes.cube_instance_id(conn, cube_id=CUBE_ID, instance_id=INSTANCE_ID)

        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
