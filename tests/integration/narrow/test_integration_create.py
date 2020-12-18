import unittest
from datetime import datetime

import pandas as pd
from mstrio.cube import Cube
from mstrio.dataset import Dataset

from ..resources import mstr_connect as con
from ..resources import mstr_create as crt
from ..resources import mstr_import as imp
from ..resources.commons import read_configs


class TestCreate(unittest.TestCase):
    def setUp(self):
        general_config_path = "production/tests/resources/general_configs2.json"
        general_configs = read_configs(general_config_path)
        self.url = general_configs["env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["password"]
        self.login_mode = general_configs["login_mode"]
        self.project_id = general_configs["project_id"]
        self.connection = con.get_connection(
            url=self.url,
            username=self.username,
            password=self.password,
            project_id=self.project_id,
            login_mode=self.login_mode,
        )

        self.cube_100k_30C_id = "F136E47011EA8A11D9A00080EF95872D"
        self.cube_200k_30C_id = "E1AA05C011EB1EA70E730080EFD5F1BC"
        self.cube_iris_id = "96FBB43711EA81BA6D5D0080EF358562"
        self.test_folder_id = "B788EF3211EAC77160A90080EFC52142"

    def test_cube_export(self):
        """TC65912"""
        connection = con.get_connection(
            self.url, self.username, self.password, self.project_id, self.login_mode
        )

        dataframe_data = {"a": [1, 2, 3], "b": ["one", "two", "three"]}

        cube_100k_30C_df = imp.get_cube_dataframe(connection, self.cube_100k_30C_id)
        self.assertEqual(cube_100k_30C_df.shape, (100000, 30))
        cube_200k_30C_df = imp.get_cube_dataframe(connection, self.cube_200k_30C_id)
        self.assertEqual(cube_200k_30C_df.shape, (200000, 30))
        cube_iris_df = imp.get_cube_dataframe(connection, self.cube_iris_id)
        self.assertEqual(cube_iris_df.shape, (201, 6))

        new_dataframe = crt.get_cube_from_dataframe(
            connection=connection, dataframe_data=dataframe_data
        ).to_dataframe()
        self.assertEqual(new_dataframe.shape, (3, 2))

        df_data_no_metric_to_attribute = ["b"]
        df_data_no_attribute = {"a": [1, 2, 3]}
        df_data_no_attribute_to_metric = ["a"]

        cube_name = "dataset_no_metric_{}".format(datetime.now().strftime("%y_%m_%d_%H_%M_%S_%f"))
        cube_no_metric = crt.get_cube_from_dataframe(
            connection=connection,
            dataframe_data={"b": ["one", "two", "three"]},
            folder_id=self.test_folder_id,
            cube_name=cube_name,
            table_name="table_no_metric",
            to_metric=None,
            to_attribute=["b"],
            update_policy="add",
        )
        self.assertEqual(len(cube_no_metric.metrics), 0)
        self.assertEqual(len(cube_no_metric.attributes), 1)

        cube_name = "dataset_no_attribute_{}".format(datetime.now().strftime("%y_%m_%d_%H_%M_%S_%f"))
        cube_no_attribute = crt.get_cube_from_dataframe(
            connection=connection,
            dataframe_data={"a": [1, 2, 3]},
            folder_id=self.test_folder_id,
            cube_name=cube_name,
            table_name="table_no_attribute",
            to_metric=["a"],
            to_attribute=None,
            update_policy="add",
        )
        self.assertEqual(len(cube_no_attribute.metrics), 1)
        self.assertEqual(len(cube_no_attribute.attributes), 0)
