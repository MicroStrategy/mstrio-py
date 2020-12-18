import time
from unittest import TestCase

import pandas as pd
import requests
from mstrio.admin.user import User, create_users_from_csv, list_users
from mstrio.api import authentication

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestUserCreationAndManagement(TestCase):
    """TC67374"""

    def setUp(self):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])
        self.user_csv_path = config_paths["user_csv"]

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

        self.user1 = None

    def test_user_creation_and_user_group_management(self):
        self.create_user_list_all_users_and_verify()
        self.delete_user_and_verify()
        self.load_user_from_CSV_file()
        self.create_user_with_the_same_username_as_in_the_csv_file()
        self.get_list_of_users_along_with_user_properties()
        self.update_user_password_and_login_with_changed_password()
        self.disconnect_user_connection_and_check_status()
        self.get_privileges_for_specified_user()

    def create_user_list_all_users_and_verify(self):
        self.user1 = User.create(self.connection, 'integration test user', 'integration test user')
        self.assertIn(self.user1.id, list_users(self.connection))

    def delete_user_and_verify(self):
        self.user1.delete(force=True)
        self.assertNotIn(self.user1.id, list_users(self.connection))

    def load_user_from_CSV_file(self):
        self.user1 = create_users_from_csv(self.connection, self.user_csv_path)[0]
        self.old_password = pd.read_csv(self.user_csv_path).loc[0, "password"]

    def create_user_with_the_same_username_as_in_the_csv_file(self):
        username = self.user1.username
        self.assertRaises(requests.exceptions.HTTPError,
                          User.create,
                          self.connection,
                          username,
                          username,
                          "redundant_password")

    def get_list_of_users_along_with_user_properties(self):
        users = list_users(self.connection)
        for user in users[:3]:  # limit list of users for faster test
            user.fetch()
            info = user.list_properties()
            self.assertIn("memberships", info.keys())

    def update_user_password_and_login_with_changed_password(self):
        new_password = "mstr1234"
        self.user1.alter(require_new_password=False)
        self.user1.alter(password=new_password)
        time.sleep(1)
        self.connection = con.get_connection(
            url=self.env_url,
            username=self.user1.username,
            password=new_password,
            login_mode=self.login_mode,
            project_id=None,
        )

    def disconnect_user_connection_and_check_status(self):
        self.connection.close()
        status = authentication.session_status(connection=self.connection)
        status_code = status.status_code
        self.assertNotEqual(status_code, 200)
        self.connection = con.get_connection(
            url=self.env_url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id=None,
        )

    def get_privileges_for_specified_user(self):
        self.user1.fetch()
        info = self.user1.list_properties()
        self.assertIn("privileges", info.keys())

    def tearDown(self) -> None:
        if self.user1 is None:
            users = list_users(self.connection, name_begins='integration')
            for user in users:
                user.delete(force=True)
        else:
            self.user1.delete(force=True)
