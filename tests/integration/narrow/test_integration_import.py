from unittest.case import TestCase

import pandas as pd

from ..resources import mstr_connect as con
from ..resources import mstr_import as imp
from ..resources.commons import read_configs


class TestImport(TestCase):
    def setUp(self):
        general_config_path = "production/tests/resources/general_configs2.json"
        general_configs = read_configs(general_config_path)

        self.url = general_configs["env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["password"]
        self.login_mode = general_configs["login_mode"]
        self.project_id = general_configs["project_id"]
        self.ssl_verify = True
        self.connection = con.get_connection(
            url=self.url,
            username=self.username,
            password=self.password,
            project_id=self.project_id,
            login_mode=self.login_mode,
        )
        self.report_id = general_configs["dataset_ids"]["basic_report"]
        self.cube_id = general_configs["dataset_ids"]["basic_cube"]

        self.attribute_ids = self.get_ids(general_configs, "attributes", "basic_cube")
        self.metric_ids = self.get_ids(general_configs, "metrics", "basic_cube")
        self.element_ids = self.get_ids(general_configs, "elements", "basic_cube")

        self.attribute_names = self.get_ids(general_configs, "attributes", "basic_cube")
        self.metric_names = self.get_ids(general_configs, "metrics", "basic_cube")
        self.element_values = self.get_ids(general_configs, "elements", "basic_cube")

        self.data = general_configs["data"]

    def test_no_filter_import_cube(self):
        """TC58735"""
        df = imp.get_cube_dataframe(connection=self.connection, cube_id=self.cube_id)
        full_data = pd.DataFrame(self.data["basic_cube"])
        self.assertDFEqual(df, full_data)

    def test_attribute_filter_import_cube(self):
        """TC58735"""
        df = imp.get_cube_dataframe(
            connection=self.connection,
            cube_id=self.cube_id,
            attribute_filter=self.attribute_ids,
            metric_filter=[],
        )
        full_data = pd.DataFrame(self.data["basic_cube"])
        filtered_data = pd.DataFrame(self.data["basic_cube_attribute_filter"])
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_metric_filter_import_cube(self):
        """TC58735"""
        df = imp.get_cube_dataframe(
            connection=self.connection,
            cube_id=self.cube_id,
            attribute_filter=[],
            metric_filter=self.metric_ids,
        )
        full_data = pd.DataFrame(self.data["basic_cube"])
        filtered_data = pd.DataFrame(self.data["basic_cube_metric_filter"])
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_attribute_element_filter_import_cube(self):
        """TC58735"""
        df = imp.get_cube_dataframe(
            connection=self.connection,
            cube_id=self.cube_id,
            element_filter=self.element_ids,
        )
        full_data = pd.DataFrame(self.data["basic_cube"])
        filtered_data = pd.DataFrame(self.data["basic_cube_element_filter"])
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_full_filter_import_cube(self):
        """TC65908"""
        df = imp.get_cube_dataframe(
            connection=self.connection,
            cube_id=self.cube_id,
            attribute_filter=self.attribute_ids,
            metric_filter=self.metric_ids,
            element_filter=self.element_ids,
        )
        full_data = pd.DataFrame(self.data["basic_cube"])
        filtered_data = pd.DataFrame(self.data["basic_cube_full_filter"])
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_empty_attribute_filter_import_cube(self):
        """TC65908"""
        df = imp.get_cube_dataframe(
            connection=self.connection, cube_id=self.cube_id, attribute_filter=[]
        )
        full_data = pd.DataFrame(self.data["basic_cube"])
        filtered_data = pd.DataFrame(self.data["basic_cube_empty_attribute_filter"])
        self.assertEqual(df.shape[0], 1)
        self.assertEqual(df.shape[1], 1)
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_empty_metric_filter_import_cube(self):
        """TC65908"""
        df = imp.get_cube_dataframe(
            connection=self.connection, cube_id=self.cube_id, metric_filter=[]
        )
        full_data = pd.DataFrame(self.data["basic_cube"])
        filtered_data = pd.DataFrame(self.data["basic_cube_empty_metric_filter"])
        self.assertEqual(df.shape[0], 2)
        self.assertEqual(df.shape[1], 1)
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_no_filter_import_report(self):
        """TC58736"""
        df = imp.get_report_dataframe(
            connection=self.connection, report_id=self.report_id
        )
        full_data = pd.DataFrame(self.data["basic_report"])
        self.assertDFEqual(df, full_data)

    def test_attribute_filter_import_report(self):
        """TC58736"""
        df = imp.get_report_dataframe(
            connection=self.connection,
            report_id=self.report_id,
            attribute_filter=self.attribute_ids,
            metric_filter=[],
        )
        full_data = pd.DataFrame(self.data["basic_report"])
        filtered_data = pd.DataFrame(self.data["basic_report_attribute_filter"])
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_metric_filter_import_report(self):
        """TC58736"""
        df = imp.get_report_dataframe(
            connection=self.connection,
            report_id=self.report_id,
            attribute_filter=[],
            metric_filter=self.metric_ids,
        )
        full_data = pd.DataFrame(self.data["basic_report"])
        filtered_data = pd.DataFrame(self.data["basic_report_metric_filter"])
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_attribute_element_filter_import_report(self):
        """TC58736"""
        df = imp.get_report_dataframe(
            connection=self.connection,
            report_id=self.report_id,
            element_filter=self.element_ids,
        )
        full_data = pd.DataFrame(self.data["basic_report"])
        filtered_data = pd.DataFrame(self.data["basic_report_element_filter"])
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_full_filter_import_report(self):
        """TC65908"""
        df = imp.get_report_dataframe(
            connection=self.connection,
            report_id=self.report_id,
            attribute_filter=self.attribute_ids,
            metric_filter=self.metric_ids,
            element_filter=self.element_ids,
        )
        full_data = pd.DataFrame(self.data["basic_report"])
        filtered_data = pd.DataFrame(self.data["basic_report_full_filter"])
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_empty_attribute_filter_import_report(self):
        """TC65908"""
        df = imp.get_report_dataframe(
            connection=self.connection, report_id=self.report_id, attribute_filter=[]
        )
        full_data = pd.DataFrame(self.data["basic_report"])
        filtered_data = pd.DataFrame(self.data["basic_report_empty_attribute_filter"])
        self.assertEqual(df.shape[0], 1)
        self.assertEqual(df.shape[1], 1)
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def test_empty_metric_filter_import_report(self):
        """TC65908"""
        df = imp.get_report_dataframe(
            connection=self.connection, report_id=self.report_id, metric_filter=[]
        )
        full_data = pd.DataFrame(self.data["basic_report"])
        filtered_data = pd.DataFrame(self.data["basic_report_empty_metric_filter"])
        self.assertEqual(df.shape[0], 2)
        self.assertEqual(df.shape[1], 1)
        self.assertDFEqual(df, filtered_data)
        self.assertDFNotEqual(df, full_data)

    def assertDFEqual(self, left, right):
        pd.testing.assert_frame_equal(left, right)

    def assertDFNotEqual(self, left, right):
        try:
            self.assertDFEqual(left, right)
        except AssertionError:
            pass
        else:
            raise AssertionError(
                "Expected different DataFrames. DataFrames are not equal"
            )

    @staticmethod
    def get_ids(config, key, dataset):
        output = config[key][dataset]
        output = map(lambda x: x["id"], output)
        output = list(output)
        return output
