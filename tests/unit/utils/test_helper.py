from mstrio.utils import helper
from unittest.mock import Mock, MagicMock
from unittest import TestCase
import json


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

        response = MagicMock()
        response.status_code = 404
        response.json.return_value = {'code': 'ERR001',
                                      'message': 'error message'}
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

    def test_filter_list_of_dicts(self):
        """
        example dict: [{'id': 'C1098775AB73C186E4666DE43453896A:-1:ZW52LTIxNDU3OGxhaW91c2Ux',
            'parentId': '',
            'username': 'Administrator',
            'userFullName': 'Administrator',
            'projectIndex': -1,
            'projectId': '',
            'projectName': '',
            'openJobsCount': 0,
            'applicationType': 'DSSScheduler',
            'dateConnectionCreated': '2020-08-03T12:20:00.000+0000',
            'dateFirstJobSubmitted': '2020-08-03T12:20:00.000+0000',
            'dateLastJobSubmitted': '2020-08-03T12:30:01.000+0000',
            'duration': 938,
            'sessionId': 'C1098775AB73C186E4666DE43453896A',
            'client': '<Scheduler>',
            'configLevel': True}]
        """

        with open('production/tests/resources/api-responses/misc/filter_list_of_dicts.json', 'r') as f:
            list_of_dicts = json.load(f)

        self.assertEqual(helper.filter_list_of_dicts(list_of_dicts, openJobsCount=[0, 1, 2]), list_of_dicts)
        self.assertEqual(helper.filter_list_of_dicts(list_of_dicts, openJobsCount=['0', '1', '2']), list_of_dicts)
        self.assertEqual(helper.filter_list_of_dicts(
            list_of_dicts, id='C1098775AB73C186E4666DE43453896A:-1:ZW52LTIxNDU3OGxhaW91c2Ux'), list_of_dicts[0:1])
        self.assertEqual(helper.filter_list_of_dicts(list_of_dicts, projectName=[
                         'LastApp0', 'LastApp01']), list_of_dicts[8:10])
        self.assertEqual(helper.filter_list_of_dicts(list_of_dicts, duration="<200"), list_of_dicts[5:6])
        self.assertEqual(helper.filter_list_of_dicts(list_of_dicts, duration="!=200"), list_of_dicts)
        self.assertEqual(helper.filter_list_of_dicts(list_of_dicts, duration="=200"), [])
        self.assertEqual(helper.filter_list_of_dicts(list_of_dicts, duration="190"), list_of_dicts[5:6])
        self.assertEqual(helper.filter_list_of_dicts(list_of_dicts, duration=190), list_of_dicts[5:6])
        self.assertEqual(helper.filter_list_of_dicts(list_of_dicts, configLevel=False), list_of_dicts[8:10])
        self.assertEqual(len(helper.filter_list_of_dicts(list_of_dicts,
                                                         dictParam={'id': '123456'})), 3)

        with self.assertRaises(TypeError):
            helper.filter_list_of_dicts(list_of_dicts, sessionId=('x', 'DDD'))
        with self.assertRaises(ValueError):
            helper.filter_list_of_dicts(list_of_dicts, duration="")
        with self.assertRaises(KeyError):
            helper.filter_list_of_dicts(list_of_dicts, newParamList="xD")
        with self.assertRaises(TypeError):
            helper.filter_list_of_dicts(list_of_dicts, configLevel={'id': '123'})
