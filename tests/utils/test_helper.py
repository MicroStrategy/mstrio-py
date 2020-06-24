from mstrio.utils import helper
from unittest.mock import Mock
from unittest import TestCase


class TestHelper(TestCase):
    def test_url_check(self):
        with self.assertRaises(Exception):
            helper.url_check('www.no_https_prefix.com')
        with self.assertRaises(Exception):
            helper.url_check('htpt://no_https_prefix.com')
        with self.assertRaises(Exception):
            helper.url_check('no_https_prefix.com')
        helper.url_check('https://env-myenv.com/path')
        helper.url_check('https://env-myenv.com/api')
        helper.url_check('https://env-myenv.com/')
        helper.url_check('https://env-myenv.com')

    def test_exception_handler(self):
        with self.assertRaises(Exception):
            helper.exception_handler('', throw_error=True)
        helper.exception_handler('', exception_type=Warning, throw_error=False)

    def test_response_handler(self):
        with self.assertWarns(Warning):
            response = Mock()
            response.status_code = 204
            helper.response_handler(response=response, msg='')

        response = Mock()
        response.status_code = 404
        helper.response_handler(response=response, msg='', throw_error=True)
        self.assertTrue(response.raise_for_status.called)

    def test_get_parallel_number(self):
        helper.os = Mock()
        helper.os.cpu_count.return_value = 2
        self.assertEqual(helper.get_parallel_number(100), 6)
        self.assertEqual(helper.get_parallel_number(1), 1)
        helper.os.cpu_count.return_value = 4
        self.assertEqual(helper.get_parallel_number(100), 8)
        self.assertEqual(helper.get_parallel_number(1), 1)
        helper.os.cpu_count.return_value = 8
        self.assertEqual(helper.get_parallel_number(100), 8)
        self.assertEqual(helper.get_parallel_number(1), 1)
        helper.os.cpu_count.return_value = 12
        self.assertEqual(helper.get_parallel_number(100), 8)
        self.assertEqual(helper.get_parallel_number(1), 1)
