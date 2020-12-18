from unittest.case import TestCase

import pandas as pd

from ..resources import mstr_connect as con
from ..resources import mstr_create as crt
from ..resources import mstr_import as imp
from ..resources import mstr_update as upd
from ..resources.commons import read_configs


class TestUpdate(TestCase):
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
        self.report_id = general_configs["report_id"]
        # self.cube_id = general_configs["cube_id"]
        self.cube_id = general_configs["dataset_ids"]["basic_cube"]
        self.cube_name = general_configs["dataset_names"]["basic_cube"]
        self.table_name = general_configs["table_names"]["basic_cube"][0]
        self.data = pd.DataFrame(general_configs["data"]["basic_cube"])
        self.modifications = general_configs["modifications"]["basic_cube"]

        self.update_cube_ids = general_configs["update_cube_ids"]

    def test_update_cube_add(self):
        """TC63496"""
        modification = self.modifications["add"]
        downloaded_file_df = imp.get_cube_dataframe(self.connection, self.cube_id)
        original_shape = downloaded_file_df.shape
        # change values which will be added to the original cube
        locally_modified_df = pd.DataFrame(
            {**modification["attribute"], **modification["metric"]}
        )
        dataset_id = crt.create_cube(
            self.connection, downloaded_file_df, "update_add_TC63496", "table1"
        )
        upd.update_cube(
            self.connection,
            locally_modified_df,
            dataset_id,
            "table1",
            update_policy="add",
        )
        updated_cube = imp.get_cube_dataframe(self.connection, dataset_id)
        modified_attributes = list(modification["attribute"].keys())
        for attribute in modified_attributes:
            new_values = set(locally_modified_df[attribute]).difference(
                downloaded_file_df[attribute]
            )
            added_rows = updated_cube[attribute].isin(new_values)

            self.assertDFEqual(
                downloaded_file_df.reset_index(drop=True),
                updated_cube[~added_rows].reset_index(drop=True),
            )
            self.assertNotEmpty(updated_cube[added_rows])

    def test_update_cube_update(self):
        """TC63498"""
        modification = self.modifications["update"]
        downloaded_file_df = imp.get_cube_dataframe(self.connection, self.cube_id)
        original_shape = downloaded_file_df.shape
        locally_modified_df = pd.DataFrame(
            {**modification["attribute"], **modification["metric"]}
        )
        dataset_id = crt.create_cube(
            self.connection, downloaded_file_df, "update_update_TC63498", "table1"
        )
        upd.update_cube(
            self.connection,
            locally_modified_df,
            dataset_id,
            "table1",
            update_policy="update",
        )
        updated_cube = imp.get_cube_dataframe(self.connection, dataset_id)
        modified_attributes = list(modification["attribute"].keys())
        for attribute in modified_attributes:
            unique_elements = set(modification["attribute"][attribute])
            original_values = downloaded_file_df[attribute]
            modified_elements = unique_elements.intersection(original_values)
            old_common_rows = downloaded_file_df[attribute].isin(modified_elements)
            new_common_rows = updated_cube[attribute].isin(modified_elements)

            self.assertDFEqual(
                downloaded_file_df[~old_common_rows], updated_cube[~new_common_rows]
            )
            self.assertDFNotEqual(
                downloaded_file_df[old_common_rows], updated_cube[new_common_rows]
            )

    def test_update_cube_upsert(self):
        """TC63501"""
        modification = self.modifications["upsert"]
        downloaded_file_df = imp.get_cube_dataframe(self.connection, self.cube_id)
        original_shape = downloaded_file_df.shape
        # modify metric and attribute
        locally_modified_df = pd.DataFrame(
            {**modification["attribute"], **modification["metric"]}
        )
        dataset_id = crt.create_cube(
            self.connection, downloaded_file_df, "update_upsert_TC63501", "table1"
        )
        upd.update_cube(
            self.connection,
            locally_modified_df,
            dataset_id,
            "table1",
            update_policy="upsert",
        )
        updated_cube = imp.get_cube_dataframe(self.connection, dataset_id)

        common_values = pd.merge(
            downloaded_file_df, updated_cube, "inner"
        ).values.tolist()
        pd.testing.assert_frame_equal(
            locally_modified_df, pd.merge(locally_modified_df, updated_cube)
        )
        self.assertTrue(common_values)

    def test_update_cube_replace_(self):
        """TC63494"""
        downloaded_file_df = imp.get_cube_dataframe(self.connection, self.cube_id)
        locally_modified_df = upd.modify_locally(downloaded_file_df, "Third", "BEST")
        locally_modified_df = upd.modify_locally(downloaded_file_df, 3712, 10000)
        dataset_id = crt.create_cube(
            self.connection, downloaded_file_df, "update_replace_TC63494", "table1"
        )
        upd.update_cube(
            self.connection,
            locally_modified_df,
            dataset_id,
            "table1",
            update_policy="replace",
        )
        updated_cube = imp.get_cube_dataframe(self.connection, dataset_id)
        updated_cube.sort_values(inplace=True, by=updated_cube.columns.to_list())
        locally_modified_df.sort_values(
            inplace=True, by=locally_modified_df.columns.to_list()
        )
        self.assertDFEqual(updated_cube, locally_modified_df)

    def update_with_modified_locally(
        self,
        initial_value,
        replacing_value,
        column_name,
        cube_id,
        table_name,
        update_policy,
    ):
        main_df = imp.get_cube_dataframe(self.connection, cube_id)
        locally_modified_df = main_df
        if locally_modified_df.at[0, column_name] == replacing_value:
            initial_value, replacing_value = replacing_value, initial_value
        locally_modified_df = upd.modify_locally(
            locally_modified_df, initial_value, replacing_value
        )
        self.assertDFNotEqual(main_df, locally_modified_df)
        upd.update_cube(
            connection=self.connection,
            new_data=locally_modified_df,
            cube_id=cube_id,
            table_name=table_name,
            update_policy=update_policy,
        )
        main_df = imp.get_cube_dataframe(self.connection, cube_id)
        self.assertDFEqual(main_df, locally_modified_df)

    def update_with_modified_locally_add_row(
        self,
        values_to_add,
        columns_to_add,
        cube_id,
        table_name,
        update_policy,
        ignore_index_to_add=True,
    ):
        main_df = imp.get_cube_dataframe(self.connection, cube_id)
        locally_modified_df = main_df
        locally_modified_df = upd.modify_locally_add_row(
            locally_modified_df,
            values_to_add,
            columns_to_add,
            ignore_index=ignore_index_to_add,
        )
        self.assertDFNotEqual(main_df, locally_modified_df)
        upd.update_cube(
            connection=self.connection,
            new_data=locally_modified_df,
            cube_id=cube_id,
            table_name=table_name,
            update_policy=update_policy,
        )
        main_df = imp.get_cube_dataframe(self.connection, cube_id)
        self.assertDFEqual(main_df, locally_modified_df)

    def test_update_cube_replace_update_upsert_add(self):
        """TC65920"""
        self.update_with_modified_locally(
            initial_value="b",
            replacing_value="c",
            column_name="B",
            cube_id=self.update_cube_ids[0],
            table_name="A.",
            update_policy="replace",
        )

        self.update_with_modified_locally(
            initial_value=2,
            replacing_value=3,
            column_name="F",
            cube_id=self.update_cube_ids[1],
            table_name="B.",
            update_policy="update",
        )

        self.update_with_modified_locally_add_row(
            values_to_add=["h", "g", 3],
            columns_to_add=list("HGI"),
            cube_id=self.update_cube_ids[2],
            table_name="C.",
            update_policy="upsert",
        )

        self.update_with_modified_locally_add_row(
            values_to_add=["j", "k", 4],
            columns_to_add=list("JKL"),
            cube_id=self.update_cube_ids[3],
            table_name="D.",
            update_policy="add",
        )

    def assertDFNotEqual(self, left, right):
        try:
            pd.testing.assert_frame_equal(left, right)
        except AssertionError:
            pass
        else:
            raise AssertionError("Expected different data frames are equal")

    def assertDFEqual(self, left, right):
        pd.testing.assert_frame_equal(left, right)

    def assertNotEmpty(self, dataframe):
        try:
            self.assertTrue(len(dataframe) > 0)
        except AssertionError:
            raise AssertionError("Expected dataframe not empty is empty")
