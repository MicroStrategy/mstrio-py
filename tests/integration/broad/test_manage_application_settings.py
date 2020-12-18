import os
import time
from datetime import datetime
from unittest import TestCase

from mstrio.admin.application import Application, Environment
from mstrio.connection import Connection
from mstrio.utils import helper
from mstrio.utils.helper import camel_to_snake

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestManageApplicationSettings(TestCase):
    """TC67028."""

    def setUp(self) -> None:
        config_paths = read_configs("production/tests/integration/resources/config_paths.json")
        general_configs = read_configs(config_paths["general_configs"])
        self.input_settings_path1 = config_paths["default_app_settings"]
        self.input_settings_path2 = config_paths["changed_app_settings"]
        self.output_csv_path = config_paths["application_settings_output_csv_path"]
        self.output_json_path = config_paths["application_settings_output_json_path"]
        self.output_pickle_path = config_paths["application_settings_output_pickle_path"]

        self.env_url = general_configs["env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["password"]
        self.login_mode = general_configs["login_mode"]
        self.env_name = general_configs["env_name"]
        self.tutorial_id = general_configs["project_id"]

        self.connection = con.get_connection(
            url=self.env_url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id=None,
        )
        self.env = Environment(self.connection)
        self.existing_app = Application(self.connection, id=self.tutorial_id)
        self.existing_app._SETTABLE_ATTRIBUTES.extend(
            list(
                helper.camel_to_snake(
                    self.existing_app.settings.list_properties()
                ).keys())
        )

        required_settings = camel_to_snake(read_configs(self.input_settings_path1))
        # for key in required_settings:
        #     self.existing_app.__setattr__(key, required_settings[key])
        # self.existing_app.update_settings()
        # self.existing_app.update_properties()

    def tearDown(self):
        try:
            os.remove("temp_app_settings.json")
        except FileNotFoundError as e:
            print(f"File {e} cannot be removed")

        self.connection.close()

    def test_manage_application_settings(self) -> None:
        self.create_and_focus_application()
        self.verify_application_info()
        self.log_in_to_application()
        self.idle_and_resume_application()
        self.apply_update_and_fetch_new_settings()
        self.export_to_supported_formats_import_and_verify()
        self.create_and_focus_application()
        self.compare_new_settings_with_previously_dumped_data()
        self.change_settings(self.input_settings_path1)
        self.verify_settings_info()

    def change_settings(self, settings_path):
        app = self.existing_app
        app.settings.import_from(file=settings_path)
        initial_settings = app.settings.list_properties()

        initial_value = app.settings.maxReportResultRowCount.value
        app.settings.maxReportResultRowCount = 40000
        self.assertEqual(app.settings.maxReportResultRowCount.value, 40000)

        app.settings.to_json(name="temp_app_settings.json")
        app.settings.import_from("temp_app_settings.json")
        self.assertEqual(app.settings.maxReportResultRowCount.value, 40000)
        app.settings.maxReportResultRowCount = initial_value
        self.assertDictEqual(app.settings.list_properties(), initial_settings)

    def apply_update_and_fetch_new_settings(self) -> None:
        app = self.existing_app
        app.settings.import_from(file=self.input_settings_path1)
        app.update_settings()
        app.fetch_settings()
        old_settings = app.settings.__dict__
        app.settings.import_from(file=self.input_settings_path2)
        app.update_settings()
        app.fetch_settings()
        new_settings = app.settings.__dict__
        self.assertNotEqual(
            old_settings.values(),
            new_settings.values(),
            msg="Please verify test settings in files {} and {} have different values".format(
                self.input_settings_path1, self.input_settings_path2
            ),
        )  # noqa

    def export_to_supported_formats_import_and_verify(self) -> None:
        # assigning known values
        app = self.existing_app
        app.settings.import_from(file=self.input_settings_path1)
        fix_settings = app.settings.__dict__
        ops = [
            (
                app.settings.to_csv,
                app.settings.import_from,
                self.output_csv_path,
            ),
            (
                app.settings.to_json,
                app.settings.import_from,
                self.output_json_path,
            ),
            (
                app.settings.to_pickle,
                app.settings.import_from,
                self.output_pickle_path,
            ),
        ]
        for export_op, import_op, file_path in ops:
            # dumping to file
            export_op(file_path)

            # assigning different known values
            app.settings.import_from(file=self.input_settings_path2)
            temporary_settings = app.settings.__dict__

            # loading from file
            import_op(file_path)
            loaded_settings = app.settings.__dict__

            self.assertNotEqual(temporary_settings.values(), loaded_settings.values())
            self.assertDictEqual(fix_settings, loaded_settings)

    def compare_new_settings_with_previously_dumped_data(self) -> None:
        # assigning known values
        app = self.existing_app
        app.settings.import_from(file=self.input_settings_path2)
        app.update_settings()
        app.fetch_settings()
        fix_settings = app.settings.__dict__
        # compare settings with JSON, Pickle, CSV (should differ)
        ops = [
            (app.settings.import_from, self.output_csv_path),
            (app.settings.import_from, self.output_json_path),
            (app.settings.import_from, self.output_pickle_path),
        ]
        for import_operation, file_path in ops:
            import_operation(file_path)
            loaded_settings = app
            app.fetch_settings()
            reverted_settings = app.settings.__dict__

            self.assertNotEqual(fix_settings, loaded_settings)
            self.assertEqual(fix_settings, reverted_settings)

    def verify_settings_info(self) -> None:
        # get settings information
        app = self.existing_app
        info = app.settings.list_properties()
        app.settings.import_from(self.input_settings_path1)
        # required_settings = read_configs(self.input_settings_path1)
        required_settings = app.settings.list_properties()
        for key in set(info).intersection(required_settings):
            self.assertDictEqual(
                {key: info.get(key)}, {key: required_settings.get(key)}
            )

    def create_and_focus_application(self) -> None:
        # TODO: we should load settings from local file to the newly created application to guarantee correct setup
        timestamp = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S%f")
        self.name = "Application " + timestamp
        self.application = self.env.create_application(
            name=self.name, force=True
        )
        self.assertTrue(self.application.is_loaded())

    def verify_application_info(self) -> None:
        info = self.application.list_properties()
        self.assertEqual(info["name"], self.name)

    def log_in_to_application(self) -> None:
        self.connection = Connection(self.env_url, self.username, self.password, project_id=self.tutorial_id)
        self.project_id = self.application.id

    def application_loading(self) -> None:
        self.application.unload()
        self.assertFalse(self.application.is_loaded())
        self.application.load()
        self.assertTrue(self.application.is_loaded())

    def get_statuses(self, nodes):
        nodes_filtered = [n for n in nodes if n["name"] == self.env_name]
        projects_filtered = [
            p
            for n in nodes_filtered
            for p in n["projects"]
            if p["id"] == self.project_id
        ]
        statuses = [p["status"] for p in projects_filtered]
        return statuses

    def idle_and_resume_application(self) -> None:
        self.application.idle(self.env_name, mode="REQUEST")
        self.application.fetch()
        nodes = self.application.nodes
        statuses2 = self.get_statuses(nodes)
        self.assertIn("request_idle", statuses2)
        self.application.resume(self.env_name)
        self.application.fetch()
        # start = time.time()
        i = 0
        while "pending" in self.get_statuses(self.application.nodes) and i < 50:
            self.application.fetch()
            time.sleep(0.5)
            i += 1

        nodes = self.application.nodes
        statuses3 = self.get_statuses(nodes)
        self.assertIn("loaded", statuses3)
        self.assertNotEqual(statuses2, statuses3)
        self.application.idle(self.env_name, mode="REQUEST")
        self.application.fetch()
        nodes = self.application.nodes
        statuses4 = self.get_statuses(nodes)
        self.assertEqual(statuses4, statuses2)
