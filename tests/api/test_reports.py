import unittest
from unittest.mock import patch
from mstrio.api import reports
from mstrio import microstrategy

USERNAME = "user"
PASSWORD = "password"
PROJECT_NAME = "MicroStrategy Tutorial"
BASE_URL = "https://env-xxxxx.customer.cloud.microstrategy.com/MicroStrategyLibrary/api"
REPORT_ID = "1"
INSTANCE_ID = "2"
OFFSET = 0
LIMIT = 1000


class TestReports(unittest.TestCase):

    @patch('mstrio.api.reports.requests.get')
    def test_report(self, mock_get):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_get.return_value.status_code = 200

        response = reports.report(conn, report_id=REPORT_ID)

        self.assertEqual(response.status_code, 200)

    @patch('mstrio.api.reports.requests.post')
    def test_report_instance(self, mock_post):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_post.return_value.status_code = 200

        response = reports.report_instance(conn, report_id=REPORT_ID, offset=OFFSET, limit=LIMIT)

        self.assertEqual(response.status_code, 200)

    @patch('mstrio.api.reports.requests.get')
    def test_report_instance_id(self, mock_get):

        conn = microstrategy.Connection(base_url=BASE_URL, username=USERNAME,
                                        password=PASSWORD, project_name=PROJECT_NAME)

        mock_get.return_value.status_code = 200

        response = reports.report_instance_id(conn, report_id=REPORT_ID, instance_id=INSTANCE_ID,
                                              offset=OFFSET, limit=LIMIT)

        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
