import pandas
import unittest
from unittest.mock import Mock, patch

from mstrio.report import Report
import json


class TestReport(unittest.TestCase):

    def setUp(self):

        with open('production/tests/api-responses/reports/report_definition.json') as f:
            self.definition = json.load(f)
        with open('production/tests/api-responses/reports/report_instance.json') as f:
            self.instance = json.load(f)
        with open('production/tests/api-responses/reports/report_instance_id.json') as f:
            self.instance_id = json.load(f)

        with open('production/tests/api-responses/reports/subtotals_definition.json') as f:
            self.sub_def = json.load(f)       
        with open('production/tests/api-responses/reports/subtotals_off.json') as f:
            self.sub_inst_off = json.load(f)
        with open('production/tests/api-responses/reports/subtotals_on.json') as f:
            self.sub_inst_on = json.load(f)

        self.report_id = self.definition["id"]
        self.report_name = self.definition["name"]
        self.connection = Mock(ok=True)
        self.connection.iserver_version = "11.1.0400"

        self.connection2 = Mock(ok=True)
        self.connection2.iserver_version = "11.2.0100"

        self.__attributes = [{"name": a["name"], "id": a["id"]} for a in
                             self.definition["definition"]["grid"]["rows"]]
        self.__metrics = [{"name": m["name"], "id": m["id"]} for m in
                          self.definition["definition"]["grid"]["columns"][-1]["elements"]]

        self.__attr_elements = [{"id": "C5456B1C11E9EDF8240A0080EF15C472:Amy", "formValues": ["Amy"]},
                                {"id": "C5456B1C11E9EDF8240A0080EF15C472:Jake",
                                    "formValues": ["Jake"]},
                                {"id": "C5456B1C11E9EDF8240A0080EF15C472:Jason",
                                    "formValues": ["Jason"]},
                                {"id": "C5456B1C11E9EDF8240A0080EF15C472:Molly",
                                    "formValues": ["Molly"]},
                                {"id": "C5456B1C11E9EDF8240A0080EF15C472:Tina", "formValues": ["Tina"]}]
        self.attr_elements = [{'id': 'DF29C0E811EA1DC167490080EF851345:Lódź',
                               'formValues': ['Lódź']},
                              {'id': 'DF29C0E811EA1DC167490080EF851345:Poznan', 'formValues': [
                                  'Poznan']},
                              {'id': 'DF29C0E811EA1DC167490080EF851345:Sosnowiec',
                               'formValues': ['Sosnowiec']},
                              {'id': 'DF29C0E811EA1DC167490080EF851345:Warszawa',
                               'formValues': ['Warszawa']},
                              {'id': 'E5A2574611EA1DC167490080EF459548:Adam',
                               'formValues': ['Adam', 'Lach']},
                              {'id': 'E5A2574611EA1DC167490080EF459548:Ignacy',
                               'formValues': ['Ignacy', 'Hologa']},
                              {'id': 'E5A2574611EA1DC167490080EF459548:Oskar',
                               'formValues': ['Oskar', 'Hologa']},
                              {'id': 'E5A2574611EA1DC167490080EF459548:Piotr',
                               'formValues': ['Piotr', 'Hologa']},
                              {'id': 'E5A2574611EA1DC167490080EF459548:Wojciech',
                               'formValues': ['Wojciech', 'Hologa']}]
        self.__headers = {"x-mstr-total-count": "28"}
        self.__selected_attr = ["DF29C0E811EA1DC167490080EF851345"]
        self.__selected_metrs = ["DF29B0F811EA1DC167490080EF851345"]
        self.__selected_elem = [
            "E5A2574611EA1DC167490080EF459548:Ignacy", "E5A2574611EA1DC167490080EF459548:Oskar"]

    @patch("mstrio.api.reports.report_instance")
    @patch("mstrio.api.reports.report_single_attribute_elements")
    @patch("mstrio.api.reports.report_definition")
    def test_init_report(self, mock_definition, mock_attr_element, mock_instance):
        """Test that definition of the report is assigned properly when report is initialized."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.definition
        mock_attr_element.return_value = Mock(headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.attr_elements

        report = Report(connection=self.connection, report_id=self.report_id)

        self.assertEqual(report._connection, self.connection)
        self.assertEqual(report._report_id, self.report_id)
        self.assertEqual(report.name, self.report_name)

        self.assertEqual(report.attributes, self.__attributes)
        self.assertEqual(report.metrics, self.__metrics)
        self.assertEqual(report._attr_elements, [])

        self.assertIsNone(report.selected_attributes)
        self.assertIsNone(report.selected_metrics)
        self.assertIsNone(report.selected_attr_elements)
        self.assertIsNone(report._dataframe)
        with self.assertWarns(Warning):
            report.dataframe

    @patch("mstrio.api.reports.report_single_attribute_elements")
    @patch("mstrio.api.reports.report_single_attribute_elements_coroutine")
    @patch("mstrio.api.reports.report_definition")
    def test_apply_filters(self, mock_definition, mock_attr_element_coroutine, mock_attr_element):
        """Test that selected objects are assigned properly when filter is applied."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.attr_elements
        mock_attr_element_coroutine.return_value = Mock()
        mock_attr_element_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element_coroutine.return_value.result.return_value.json.return_value = self.attr_elements

        report = Report(connection=self.connection, report_id=self.report_id)
        report.apply_filters(self.__selected_attr, self.__selected_metrs, self.__selected_elem)

        self.assertTrue(mock_attr_element_coroutine.called)
        self.assertEqual(report.selected_attributes, self.__selected_attr)
        self.assertEqual(report.selected_metrics, self.__selected_metrs)
        self.assertEqual(report.selected_attr_elements, self.__selected_elem)

        report = Report(connection=self.connection, report_id=self.report_id)
        report.apply_filters(attributes=[], metrics=[])
        self.assertEqual(report.selected_attr_elements, None)
        self.assertEqual(report._filter.attr_selected, [])
        self.assertEqual(report._filter.metr_selected, [])

    @patch("mstrio.api.reports.report_instance")
    @patch("mstrio.api.reports.report_single_attribute_elements")
    @patch("mstrio.api.reports.report_single_attribute_elements_coroutine")
    @patch("mstrio.api.reports.report_definition")
    def test_clear_filters(self, mock_definition, mock_attr_element_coroutine, mock_attr_element, mock_instance):
        """Test that selected objects are assigned with empty lists when filter is cleared."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.attr_elements
        mock_attr_element_coroutine.return_value = Mock()
        mock_attr_element_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element_coroutine.return_value.result.return_value.json.return_value = self.attr_elements

        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.instance

        report = Report(connection=self.connection, report_id=self.report_id)
        report.apply_filters(self.__selected_attr,
                             self.__selected_metrs, self.__selected_elem)

        self.assertEqual(report.selected_attributes, self.__selected_attr)
        self.assertEqual(report.selected_metrics, self.__selected_metrs)
        self.assertEqual(report.selected_attr_elements, self.__selected_elem)

        report.clear_filters()

        self.assertIsNone(report.selected_attributes)
        self.assertIsNone(report.selected_metrics)
        self.assertIsNone(report.selected_attr_elements)

    @patch("mstrio.api.reports.report_instance_id")
    @patch("mstrio.api.reports.report_instance_id_coroutine")
    @patch("mstrio.api.reports.report_instance")
    @patch("mstrio.api.reports.report_single_attribute_elements")
    @patch("mstrio.api.reports.report_single_attribute_elements_coroutine")
    @patch("mstrio.api.reports.report_definition")
    def test_to_dataframe(self, mock_definition, mock_attr_element_coroutine, mock_attr_element, mock_instance, mock_instance_id_coroutine, mock_instance_id):
        """Test that data is retrieved and parsed properly when to_dataframe() is called.
        Result should be saved to Report.dataframe property.
        """

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.attr_elements
        mock_attr_element_coroutine.return_value = Mock()
        mock_attr_element_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element_coroutine.return_value.result.return_value.json.return_value = self.attr_elements

        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.instance
        mock_instance_id.return_value = Mock(ok=True)
        mock_instance_id.return_value.json.return_value = self.instance_id
        mock_instance_id_coroutine.return_value = Mock()
        mock_instance_id_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_instance_id_coroutine.return_value.result.return_value.json.return_value = self.instance_id

        report = Report(connection=self.connection, report_id=self.report_id)
        df = report.to_dataframe(limit=3)

        self.assertTrue(mock_instance.called)
        self.assertTrue(mock_instance_id_coroutine.called)
        self.assertIsInstance(df, pandas.core.frame.DataFrame)
        self.assertIsInstance(report.dataframe, pandas.core.frame.DataFrame)
        self.assertEqual(df.IQ.sum(), 29349845.567647062)
        self.assertEqual(df.salary.sum(), 4145784.7926787906)

    @patch("mstrio.api.reports.report_instance")
    @patch("mstrio.api.reports.report_single_attribute_elements")
    @patch("mstrio.api.reports.report_single_attribute_elements_coroutine")
    @patch("mstrio.api.reports.report_definition")
    def test_apply_filters_for_incorrect_assignments(self, mock_definition, mock_attr_element_coroutine, mock_attr_element, mock_instance):
        """Test that incorrectly assigned selected objects are assigned properly when filter is applied."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.attr_elements
        mock_attr_element_coroutine.return_value = Mock()
        mock_attr_element_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element_coroutine.return_value.result.return_value.json.return_value = self.attr_elements

        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.instance

        report = Report(connection=self.connection, report_id=self.report_id)
        # attributes assigned selected_metrs, metrics assigned selected_elem and attr_elements assigned selected_attr
        report.apply_filters(attributes=self.__selected_metrs,
                             metrics=self.__selected_elem,
                             attr_elements=self.__selected_attr)

        self.assertEqual(report.selected_attributes, self.__selected_attr)
        self.assertEqual(report.selected_metrics, self.__selected_metrs)
        self.assertEqual(report.selected_attr_elements, self.__selected_elem)

    @patch("mstrio.api.reports.report_instance")
    @patch("mstrio.api.reports.report_single_attribute_elements")
    @patch("mstrio.api.reports.report_single_attribute_elements_coroutine")
    @patch("mstrio.api.reports.report_definition")
    def test_apply_filters_no_list(self, mock_definition, mock_attr_element_coroutine, mock_attr_element, mock_instance):
        """Test that selected objects passed as strings are assigned properly when filter is applied."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.attr_elements
        mock_attr_element_coroutine.return_value = Mock()
        mock_attr_element_coroutine.return_value.result.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element_coroutine.return_value.result.return_value.json.return_value = self.attr_elements

        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.instance

        report = Report(connection=self.connection, report_id=self.report_id)
        report.apply_filters(attributes=self.__selected_attr[0],
                             metrics=self.__selected_metrs[0],
                             attr_elements=self.__selected_elem[0])

        self.assertEqual(report.selected_attributes, self.__selected_attr)
        self.assertEqual(report.selected_metrics, self.__selected_metrs)
        self.assertEqual(report.selected_attr_elements, self.__selected_elem[:1])

    @patch("mstrio.api.reports.report_instance")
    @patch("mstrio.api.reports.report_single_attribute_elements")
    @patch("mstrio.api.reports.report_definition")
    def test_apply_filters_invalid_elements(self, mock_definition, mock_attr_element, mock_instance):
        """Test that invalid id passed to a filter raises ValueError."""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.definition
        mock_attr_element.return_value = Mock(ok=True, headers=self.__headers)
        mock_attr_element.return_value.json.return_value = self.attr_elements
        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.instance

        report = Report(connection=self.connection, report_id=self.report_id)
        self.assertRaises(ValueError, report.apply_filters,
                          attributes="INV123456")

    @patch("mstrio.api.reports.report_instance")
    @patch("mstrio.api.reports.report_definition")
    def test_subtotals(self, mock_definition, mock_instance):
        """Test that subtotals are correctly turned off from requests"""

        mock_definition.return_value = Mock(ok=True)
        mock_definition.return_value.json.return_value = self.sub_def
        mock_instance.return_value = Mock(ok=True)
        mock_instance.return_value.json.return_value = self.sub_inst_off

        report = Report(connection=self.connection2, report_id="7405D8DE11EA482779D20080EF152878")
        df = report.to_dataframe()
        self.assertTupleEqual(df.shape, (26, 7))

        mock_instance.return_value.json.return_value = self.sub_inst_on

        report_with_subtotals = Report(connection=self.connection, report_id="7405D8DE11EA482779D20080EF152878")
        df_ws = report_with_subtotals.to_dataframe()
        self.assertTupleEqual(df_ws.shape, (35, 7))
        self.assertFalse(df.equals(df_ws))


if __name__ == "__main__":
    unittest.main()
