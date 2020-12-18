import unittest

import pandas as pd
from mstrio.connection import Connection
from mstrio.dataset import Dataset

from ..resources.commons import read_configs


class TestErrorHandling(unittest.TestCase):
    """TC69901"""
    def setUp(self):
        general_config_path = "production/tests/resources/general_configs2.json"
        general_configs = read_configs(general_config_path)

        self.url = general_configs["env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["password"]
        self.login_mode = general_configs["login_mode"]
        self.project_id = general_configs["project_id"]
        self.connection = Connection(base_url=self.url,
                                     username=self.username,
                                     password=self.password,
                                     login_mode=self.login_mode,
                                     project_id=self.project_id)

    def test_error_handling(self):
        data = pd.DataFrame({
            'a1': [1, 2, 3],
            'a2': [11, 12, 13],
            'm': [1.0, 1.1, 1.2]
        })
        data.rename({'a2': 'a1'}, inplace=True, axis=1)

        ds = Dataset(self.connection, 'Duplicate test')
        try:
            ds.add_table(name='duplicate',
                         data_frame=data,
                         update_policy='add')
            wrng = ""
        except Exception as e:
            wrng = e
        self.assertEqual(str(wrng),
                         "DataFrame column names need to be unique for each table in the Dataset.")
