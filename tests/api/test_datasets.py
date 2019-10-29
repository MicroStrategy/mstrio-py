import unittest
from unittest.mock import patch
from mstrio.api import datasets
from mstrio import microstrategy

USERNAME = "user"
PASSWORD = "password"
PROJECT_NAME = "MicroStrategy Tutorial"
BASE_URL = "https://env-xxxxx.customer.cloud.microstrategy.com/MicroStrategyLibrary/api"
JSON_BODY = "testjson"
DATASET_ID = "1501C7F44AEFE6B66FE1BDB1954EF12D"
TABLE_ID = "1501C7F44AEFE6B66FE1BDB1954EF12D"
TABLE_NAME = "MYTABLE"
UPDATE_POLICY = "update"


class TestDatasets(unittest.TestCase):

    @patch('mstrio.api.datasets.requests.post')
    def test_create_dataset(self, mock_post):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_post.return_value.status_code = 200

        response = datasets.create_dataset(conn, body=JSON_BODY)

        self.assertEqual(response.status_code, 200)

    @patch('mstrio.api.datasets.requests.patch')
    def test_update_dataset(self, mock_patch):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_patch.return_value.status_code = 200

        response = datasets.update_dataset(conn, dataset_id=DATASET_ID, table_name=TABLE_NAME,
                                           update_policy=UPDATE_POLICY, body=JSON_BODY)

        self.assertEqual(response.status_code, 200)

    @patch('mstrio.api.datasets.requests.delete')
    def test_delete_dataset(self, mock_delete):
        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_delete.return_value.status_code = 200

        response = datasets.delete_dataset(conn, dataset_id=DATASET_ID)

        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
