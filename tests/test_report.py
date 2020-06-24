import json
import pickle
import unittest

from tests.mock_report import MockReports
from tests.mock_connection import MockConnection
from mstrio import connection
from mstrio import report


class TestReport(unittest.TestCase):
    test_df_path = 'production/tests/api-responses/reports/iris_report_dumped.pkl'
    report_info_path = 'production/tests/api-responses/reports/report_info.json'
    report_definition_path = 'production/tests/api-responses/reports/report_definition.json'

    def setUp(self):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()
        report.reports = MockReports.mock_reports_api()

        self.connection = connection.Connection(base_url='http://mocked.url.com',
                                                username='username',
                                                password='password')
        self.report_id = ''
        with open(self.test_df_path, 'rb') as f:
            self.required_df = pickle.load(f)

        with open(self.report_definition_path, 'rb') as f:
            self.report_definition_data = json.load(f)

    def test_apply_filters(self):
        tested_report = report.Report(parallel=False, connection=self.connection, report_id=self.report_id)
        tested_report.apply_filters(attributes='7BC69FAC11EA4C2060710080EFD5AA25')
        self.assertEqual(tested_report.selected_attributes, [['7BC69FAC11EA4C2060710080EFD5AA25']])
        tested_report.apply_filters(metrics='7BC6A72211EA4C2060710080EFD5AA25')
        self.assertEqual(tested_report.selected_metrics, ['7BC6A72211EA4C2060710080EFD5AA25'])
        tested_report.apply_filters(attr_elements='7BC69FAC11EA4C2060710080EFD5AA25:1')
        self.assertEqual(tested_report.selected_attr_elements, ['7BC69FAC11EA4C2060710080EFD5AA25:1'])

    def test_clear_filters(self):
        tested_report = report.Report(parallel=False, connection=self.connection, report_id=self.report_id)
        tested_report.apply_filters(attributes='7BC69FAC11EA4C2060710080EFD5AA25')
        tested_report.clear_filters()
        self.assertEqual(tested_report.selected_attributes, [])
        tested_report.apply_filters(metrics='7BC6A72211EA4C2060710080EFD5AA25')
        tested_report.clear_filters()
        self.assertEqual(tested_report.selected_metrics, [])
        tested_report.apply_filters(attr_elements='7BC69FAC11EA4C2060710080EFD5AA25:1')
        tested_report.clear_filters()
        self.assertEqual(tested_report.selected_attr_elements, [])


    def test_to_dataframe_no_filter(self):
        tested_report = report.Report(parallel=True, connection=self.connection, report_id=self.report_id)
        self.assertTrue(tested_report.to_dataframe().equals(self.required_df))
        self.assertTrue(tested_report.to_dataframe(limit=70).equals(self.required_df))
        tested_report = report.Report(parallel=False, connection=self.connection, report_id=self.report_id)
        self.assertTrue(tested_report.to_dataframe().equals(self.required_df))
        self.assertTrue(tested_report.to_dataframe(limit=70).equals(self.required_df))

    def test_to_dataframe_metric_filter(self):
        tested_report = report.Report(parallel=True, connection=self.connection, report_id=self.report_id)
        metric_id = tested_report.metrics[0]['id']
        metric_name = tested_report.metrics[0]['name']
        tested_report.apply_filters(attributes=[], metrics=metric_id)
        self.assertTrue(tested_report.to_dataframe().equals(self.required_df[[metric_name]]))
        self.assertTrue(tested_report.to_dataframe(limit=70).equals(self.required_df[[metric_name]]))
        tested_report = report.Report(parallel=False, connection=self.connection, report_id=self.report_id)
        metric_id = tested_report.metrics[0]['id']
        metric_name = tested_report.metrics[0]['name']
        tested_report.apply_filters(attributes=[], metrics=metric_id)
        self.assertTrue(tested_report.to_dataframe().equals(self.required_df[[metric_name]]))
        self.assertTrue(tested_report.to_dataframe(limit=70).equals(self.required_df[[metric_name]]))

    def test_to_dataframe_attribute_filter(self):
        tested_report = report.Report(parallel=True, connection=self.connection, report_id=self.report_id)
        tested_report.apply_filters(attributes='7BC69FAC11EA4C2060710080EFD5AA25', metrics=[])
        self.assertTrue(tested_report.to_dataframe().equals(self.required_df[['Id']]))
        self.assertTrue(tested_report.to_dataframe(limit=70).equals(self.required_df[['Id']]))
        tested_report = report.Report(parallel=False, connection=self.connection, report_id=self.report_id)
        tested_report.apply_filters(attributes='7BC69FAC11EA4C2060710080EFD5AA25', metrics=[])
        self.assertTrue(tested_report.to_dataframe().equals(self.required_df[['Id']]))
        self.assertTrue(tested_report.to_dataframe(limit=70).equals(self.required_df[['Id']]))

    def test_to_dataframe_attribute_element_filter(self):
        tested_report = report.Report(parallel=True, connection=self.connection, report_id=self.report_id)
        tested_report.apply_filters(attr_elements='7BC69FAC11EA4C2060710080EFD5AA25:1')
        self.assertTrue(tested_report.to_dataframe().equals(self.required_df[self.required_df['Id'] == '1']))
        self.assertTrue(tested_report.to_dataframe(limit=70).equals(self.required_df[self.required_df['Id'] == '1']))
        tested_report = report.Report(parallel=False, connection=self.connection, report_id=self.report_id)
        tested_report.apply_filters(attr_elements='7BC69FAC11EA4C2060710080EFD5AA25:1')
        self.assertTrue(tested_report.to_dataframe().equals(self.required_df[self.required_df['Id'] == '1']))
        self.assertTrue(tested_report.to_dataframe(limit=70).equals(self.required_df[self.required_df['Id'] == '1']))

    def test_properties(self):
        tested_report = report.Report(parallel=False, connection=self.connection, report_id=self.report_id)
        tested_df = tested_report.to_dataframe()
        self.assertTrue(tested_df.equals(tested_report.dataframe))
        tested_df = tested_report.to_dataframe()
        self.assertEqual(tested_report.name, self.report_definition_data['name'])
        self.assertCountEqual(tested_report.attributes,
                         [{'id': attr['id'],
                           'name': attr['name']} for \
                          attr in self.report_definition_data['definition']['availableObjects']['attributes']])
