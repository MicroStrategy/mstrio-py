import os
from unittest import TestCase

import pandas as pd
from mstrio.admin.application import Environment

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestManageServerSettings(TestCase):
    """TC69905"""

    @classmethod
    def setUpClass(cls):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])
        cls.url = general_configs["env_url"]
        cls.name = general_configs["username"]
        cls.pwd = general_configs["password"]
        cls.mode = general_configs["login_mode"]
        cls.connection = con.get_connection(cls.url, cls.name, cls.pwd, None, cls.mode)
        cls.env = Environment(cls.connection)

    def setUp(self):
        self.suffices = [".pkl", ".csv", ".json"]
        self.modes = ["rb", "r", "r"]

    def tearDown(self):
        for suffix in self.suffices:
            self.remove_file(suffix)

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def test_server_settings(self):
        self.change_settings_and_fetch()
        self.export_settings_to_files()
        self.import_settings_from_file_and_update()
        self.save_settings_as_df()

    def export_settings_to_files(self):
        for suffix, mode in zip(self.suffices, self.modes):
            self.export_to(suffix)
            self.read_and_assert(suffix, mode)

    def change_settings_and_fetch(self):
        previous_state = self.env.server_settings.maxInboxMsgCountPerUser.value
        self.env.server_settings.maxInboxMsgCountPerUser.value = 550
        self.env.update_settings()
        self.env.fetch_settings()
        current_state = self.env.server_settings.maxInboxMsgCountPerUser.value
        self.assertNotEqual(previous_state, current_state)
        self.env.server_settings.maxInboxMsgCountPerUser.value = previous_state
        self.env.update_settings()
        self.env.fetch_settings()
        current_state = self.env.server_settings.maxInboxMsgCountPerUser.value
        self.assertEqual(current_state, previous_state)

    def import_settings_from_file_and_update(self):
        for suffix in self.suffices:
            self.env.server_settings.import_from("server_settings" + suffix)
            self.env.update_settings()

    def save_settings_as_df(self):
        self.env.server_settings.to_dataframe()
        self.assertIsInstance(self.env.server_settings.to_dataframe(), pd.DataFrame)

    def remove_file(self, suffix):
        try:
            os.remove("server_settings" + suffix)
        except FileNotFoundError as e:
            print(f"File {e} cannot be removed")

    def read_and_assert(self, suffix, mode):
        with open("server_settings" + suffix, mode) as f:
            file_content = f.read()
            self.assertGreater(len(file_content), 0)

    def export_to(self, suffix):
        if suffix == ".pkl":
            self.env.server_settings.to_pickle("server_settings" + suffix)
        elif suffix == ".csv":
            self.env.server_settings.to_csv("server_settings" + suffix)
        else:
            self.env.server_settings.to_json("server_settings" + suffix)
