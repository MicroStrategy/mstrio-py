import pandas
import unittest
from unittest.mock import Mock, patch

from mstrio.report import Report


class TestReport(unittest.TestCase):

    def setUp(self):
        self.report_id = '1DC7D33611E9AE27F6B00080EFE52FBC'
        self.report_name = 'UnitTest'
        self.connection = "test_connection"
        self.__definition = {'id': self.report_id,
                            'name': self.report_name,
                             'result': {'definition': {'availableObjects': {'metrics': [{'name': 'Age',
                                'id': '089FB58611E9CA4D39700080EF15B5B9',
                                'type': 'Metric'},
                                {'name': 'Row Count - table1',
                                'id': '089DE7BA11E9CA4D085B0080EFC515B9',
                                'type': 'Metric'}],
                                'attributes': [{'name': 'Name',
                                'id': '089FC10C11E9CA4D39700080EF15B5B9',
                                'type': 'Attribute',
                                'forms': [{'id': '45C11FA478E745FEA08D781CEA190FE5',
                                    'name': 'ID',
                                    'dataType': 'Char',
                                    'baseFormCategory': 'ID',
                                    'baseFormType': 'Text'}]}]}}}}
        self.__instance = {'id': self.report_id,
                            'name': self.report_name,
                            'status': 1,
                            'instanceId': '49C2D26C11E9CB21237E0080EF1546B6',
                            'result': {
                                'definition': {
                                    'metrics': [{'name': 'Age',
                                        'id': '089FB58611E9CA4D39700080EF15B5B9',
                                        'type': 'Metric',
                                        'min': 18,
                                        'max': 21,
                                        'dataType': 'Integer',
                                        'numberFormatting': {'category': 9, 'formatString': 'General'}}],
                                    'attributes': [{'name': 'Name',
                                        'id': '089FC10C11E9CA4D39700080EF15B5B9',
                                        'type': 'Attribute',
                                        'forms': [{'id': '45C11FA478E745FEA08D781CEA190FE5',
                                        'name': 'ID',
                                        'dataType': 'Char',
                                        'baseFormCategory': 'ID',
                                        'baseFormType': 'Text'}]}],
                                    'thresholds': [],
                                    'sorting': []},
                            'data': {'paging': {'total': 4,
                                'current': 2,
                                'offset': 0,
                                'limit': 2,
                                'prev': None,
                                'next': None},
                            'root': {'isPartial': True,
                                'children': [{'depth': 0,
                                'element': {'attributeIndex': 0,
                                'formValues': {'ID': 'jack'},
                                'name': 'jack',
                                'id': 'hjack;089FC10C11E9CA4D39700080EF15B5B9'},
                                'metrics': {'Age': {'rv': 18, 'fv': '18', 'mi': 0}}},
                                {'depth': 0,
                                'element': {'attributeIndex': 0,
                                'formValues': {'ID': 'krish'},
                                'name': 'krish',
                                'id': 'hkrish;089FC10C11E9CA4D39700080EF15B5B9'},
                                'metrics': {'Age': {'rv': 19, 'fv': '19', 'mi': 0}}}]}}}}
        self.__instance_id = {'id': self.report_id,
                            'name': self.report_name,
                            'status': 1,
                            'instanceId': '49C2D26C11E9CB21237E0080EF1546B6',
                            'result': {
                                'definition': {
                                    'metrics': [{'name': 'Age',
                                        'id': '089FB58611E9CA4D39700080EF15B5B9',
                                        'type': 'Metric',
                                        'min': 18,
                                        'max': 21,
                                        'dataType': 'Integer',
                                        'numberFormatting': {'category': 9, 'formatString': 'General'}}],
                                    'attributes': [{'name': 'Name',
                                        'id': '089FC10C11E9CA4D39700080EF15B5B9',
                                        'type': 'Attribute',
                                        'forms': [{'id': '45C11FA478E745FEA08D781CEA190FE5',
                                        'name': 'ID',
                                        'dataType': 'Char',
                                        'baseFormCategory': 'ID',
                                        'baseFormType': 'Text'}]}],
                                'thresholds': [],
                                'sorting': []},
                            'data': {'paging': {'total': 4,
                                'current': 2,
                                'offset': 2,
                                'limit': 2,
                                'prev': None,
                                'next': None},
                            'root': {'isPartial': True,
                                'children': [{'depth': 0,
                                'element': {'attributeIndex': 0,
                                'formValues': {'ID': 'nick'},
                                'name': 'nick',
                                'id': 'hnick;089FC10C11E9CA4D39700080EF15B5B9'},
                                'metrics': {'Age': {'rv': 21, 'fv': '21', 'mi': 0}}},
                                {'depth': 0,
                                'element': {'attributeIndex': 0,
                                'formValues': {'ID': 'Tom'},
                                'name': 'Tom',
                                'id': 'hTom;089FC10C11E9CA4D39700080EF15B5B9'},
                                'metrics': {'Age': {'rv': 20, 'fv': '20', 'mi': 0}}}]}}}}

        self.__attr_elements = [{'id': '089FC10C11E9CA4D39700080EF15B5B9:jack', 'formValues': ['jack']},
                                {'id': '089FC10C11E9CA4D39700080EF15B5B9:krish', 'formValues': ['krish']},
                                {'id': '089FC10C11E9CA4D39700080EF15B5B9:nick', 'formValues': ['nick']},
                                {'id': '089FC10C11E9CA4D39700080EF15B5B9:Tom', 'formValues': ['Tom']}]
        self.__headers = {'x-mstr-total-count': '4'}
        self.__selected_attr = ['089FC10C11E9CA4D39700080EF15B5B9']
        self.__selected_metrs = ['089FB58611E9CA4D39700080EF15B5B9']
        self.__selected_elem = ['089FC10C11E9CA4D39700080EF15B5B9:Tom', '089FC10C11E9CA4D39700080EF15B5B9:jack']
        self.__dataframe = pandas.DataFrame({'Name':['jack', 'krish','nick','Tom'], 'Age':[18,19,21,20]})

    @patch('mstrio.api.reports.report_instance')
    @patch('mstrio.api.reports.report_single_attribute_elements')
    @patch('mstrio.api.reports.report')
    def test_init_report(self, mock_definition, mock_attr_element, mock_instance):
        """Test that definition of the report is assigned properly when report is initialized."""

        from mstrio.api.reports import report_instance
        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.__instance

        report = Report(connection=self.connection, report_id=self.report_id)

        self.assertTrue(mock_instance.called)
        self.assertFalse(mock_attr_element.called)
        
        self.assertEqual(report._connection, self.connection)
        self.assertEqual(report._report_id, self.report_id)
        self.assertEqual(report.name, self.report_name)

        self.assertEqual(report.attributes, [{'name': 'Name', 'id': '089FC10C11E9CA4D39700080EF15B5B9'}])
        self.assertEqual(report.metrics, [{'name': metric['name'],
                                           'id': metric['id']} \
                                          for metric in self._TestReport__instance['result']['definition']['metrics']])

        self.assertIsNone(report.selected_attributes)
        self.assertIsNone(report.selected_metrics)
        self.assertIsNone(report.selected_attr_elements)
        self.assertIsNone(report._dataframe)
        with self.assertWarns(Warning):
            report.dataframe

    @patch('mstrio.api.reports.report_instance')
    @patch('mstrio.api.reports.report_single_attribute_elements')
    @patch('mstrio.api.reports.report')
    def test_apply_filters(self, mock_definition, mock_attr_element, mock_instance):
        """Test that selected objects are assigned properly when filter is applied."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.__instance

        report = Report(connection=self.connection, report_id=self.report_id)
        report.apply_filters(self.__selected_attr, self.__selected_metrs, self.__selected_elem)

        self.assertEqual(report.selected_attributes, self.__selected_attr)
        self.assertEqual(report.selected_metrics, self.__selected_metrs)
        self.assertEqual(report.selected_attr_elements, self.__selected_elem)

        report.clear_filters()
        report.apply_filters(attributes=[], metrics=[])
        self.assertIsNone(report.selected_attributes)
        self.assertIsNone(report.selected_metrics)

    @patch('mstrio.api.reports.report_instance')
    @patch('mstrio.api.reports.report_single_attribute_elements')
    @patch('mstrio.api.reports.report')
    def test_clear_filters(self, mock_definition, mock_attr_element, mock_instance):
        """Test that selected objects are assigned with empty lists when filter is cleared."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.__instance

        report = Report(connection=self.connection, report_id=self.report_id)
        report.apply_filters(self.__selected_attr, self.__selected_metrs, self.__selected_elem)

        self.assertEqual(report.selected_attributes, self.__selected_attr)
        self.assertEqual(report.selected_metrics, self.__selected_metrs)
        self.assertEqual(report.selected_attr_elements, self.__selected_elem)

        report.clear_filters()

        self.assertIsNone(report.selected_attributes)
        self.assertIsNone(report.selected_metrics)
        self.assertIsNone(report.selected_attr_elements)

    @patch('mstrio.api.reports.report_instance_id')
    @patch('mstrio.api.reports.report_instance')
    @patch('mstrio.api.reports.report_single_attribute_elements')
    @patch('mstrio.api.reports.report')
    def test_to_dataframe(self, mock_definition, mock_attr_element, mock_instance, mock_instance_id):
        """Test that data is retrieved and parsed properly when to_dataframe() is called.
        Result should be saved to Report.dataframe property.
        """

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_instance.return_value = Mock(ok=True)        
        mock_instance.return_value.json.return_value = self.__instance
        mock_instance_id.return_value = Mock(ok=True)
        mock_instance_id.return_value.json.return_value = self.__instance_id

        report = Report(connection=self.connection, report_id=self.report_id)
        df = report.to_dataframe(limit=2)
        
        self.assertTrue(mock_instance.called)
        self.assertTrue(mock_instance_id.called)
        self.assertIsInstance(df, pandas.core.frame.DataFrame)
        self.assertIsInstance(report.dataframe, pandas.core.frame.DataFrame)
        self.assertTrue(df.equals(self.__dataframe))

    @patch('mstrio.api.reports.report_instance')
    @patch('mstrio.api.reports.report_single_attribute_elements')
    @patch('mstrio.api.reports.report')
    def test_apply_filters_for_incorrect_assignments(self, mock_definition, mock_attr_element, mock_instance):
        """Test that incorrectly assigned selected objects are assigned properly when filter is applied."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.__instance

        report = Report(connection=self.connection, report_id=self.report_id)
        # attributes assigned selected_metrs, metrics assigned selected_elem and attr_elements assigned selected_attr
        report.apply_filters(attributes=self.__selected_metrs, metrics=self.__selected_elem,
                             attr_elements=self.__selected_attr)

        self.assertEqual(report.selected_attributes, self.__selected_attr)
        self.assertEqual(report.selected_metrics, self.__selected_metrs)
        self.assertEqual(report.selected_attr_elements, self.__selected_elem)

    @patch('mstrio.api.reports.report_instance')
    @patch('mstrio.api.reports.report_single_attribute_elements')
    @patch('mstrio.api.reports.report')
    def test_apply_filters_no_list(self, mock_definition, mock_attr_element, mock_instance):
        """Test that selected objects passed as strings are assigned properly when filter is applied."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.__instance

        report = Report(connection=self.connection, report_id=self.report_id)
        report.apply_filters(attributes=self.__selected_attr[0], metrics=self.__selected_metrs[0],
                             attr_elements=self.__selected_elem[0])

        self.assertEqual(report.selected_attributes, self.__selected_attr)
        self.assertEqual(report.selected_metrics, self.__selected_metrs)
        self.assertEqual(report.selected_attr_elements, self.__selected_elem[:1])

    @patch('mstrio.api.reports.report_instance')
    @patch('mstrio.api.reports.report_single_attribute_elements')
    @patch('mstrio.api.reports.report')
    def test_apply_filters_invalid_elements(self, mock_definition, mock_attr_element, mock_instance):
        """Test that invalid id passed to a filter raises ValueError."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.__definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.__attr_elements
        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.__instance

        report = Report(connection=self.connection, report_id=self.report_id)
        self.assertRaises(ValueError, report.apply_filters, attributes='INV123456')

if __name__ == '__main__':
    unittest.main()
