from unittest import TestCase

import pandas as pd
from mstrio.admin.application import Application, Environment

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestApplicationListAndSettings(TestCase):
    """TC67029"""

    def setUp(self) -> None:
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])
        self.input_settings_path1 = config_paths["default_app_settings"]
        self.input_settings_path2 = config_paths["changed_app_settings"]
        self.output_csv_path = config_paths["application_settings_output_csv_path"]
        self.output_json_path = config_paths["application_settings_output_json_path"]
        self.output_pickle_path = config_paths[
            "application_settings_output_pickle_path"
        ]
        self.settings_wrong_keys_path = config_paths["settings_wrong_keys_path"]
        self.settings_wrong_value_types_path = config_paths[
            "settings_wrong_value_types_path"
        ]

        self.env_url = general_configs["env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["password"]
        self.login_mode = general_configs["login_mode"]
        self.env_name = general_configs["env_name"]

        self.connection = con.get_connection(
            url=self.env_url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id=None,
        )
        self.env = Environment(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_application_list_and_settings(self):
        self.get_application_list_and_verify()
        self.get_nodes_list_and_verify()
        self.get_and_compare_application_settings_info()
        self.create_dict_with_proper_format()
        self.validate_proper_format()
        self.validate_improper_format()

    def get_application_list_and_verify(self):
        self.applications = self.env.list_applications(limit=3)
        for app in self.applications:
            self.assertIsInstance(app, Application)
        self.applications = [
            Application(self.connection, app.name) for app in self.applications
        ]

    def get_nodes_list_and_verify(self):
        self.nodes = (
            self.env.list_nodes()
        )  # TODO niespojnosc z Application.nodes, tu metoda, tam atrybut
        for node in self.nodes:
            self.assertEqual(node["name"], self.env_name)

    def get_and_compare_application_settings_info(self):
        for i, app in enumerate(self.applications):
            previous_app = self.applications[i - 1]
            previous_app.fetch_settings()
            app.fetch_settings()

            # confirm settings are comparable
            comparison = self.env.compare_settings([app, previous_app])
            self.assertIsInstance(comparison, pd.DataFrame)
            self.assertEqual(comparison.shape[1], 2 + 1)

    def create_dict_with_proper_format(self):
        for app in self.applications:
            app.settings.import_from(file=self.input_settings_path1)

    def validate_proper_format(self):
        # positive test
        app = self.applications[0]
        app.settings.import_from(file=self.input_settings_path1)
        app.update_settings()

    def validate_improper_format(self):
        # negative test
        with self.assertRaises(ValueError):
            app = self.applications[0]
            app.settings.import_from(file=self.settings_wrong_keys_path)

        with self.assertRaises(ValueError):
            app = self.applications[0]
            app.settings.import_from(file=self.settings_wrong_value_types_path)
