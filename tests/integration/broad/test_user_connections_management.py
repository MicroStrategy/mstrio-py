import time
from unittest import TestCase

from mstrio.admin.user import UserConnections, list_users, User
from mstrio.connection import Connection

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestUserConnectionsManagement(TestCase):
    """TC67376"""

    def setUp(self):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])
        self.connection_configs = read_configs(config_paths["connection_configs"])

        self.env_url = general_configs["env_url"]
        self.env_name = general_configs["env_name"]
        self.login_mode = general_configs["login_mode"]
        self.project_id = general_configs["project_id"]
        self.admin_username = general_configs["username"]
        self.admin_password = general_configs["password"]
        self.connection = con.get_connection(
            url=self.env_url,
            username=self.admin_username,
            password=self.admin_password,
            login_mode=self.login_mode,
            project_id=self.project_id,
        )

        self.wait_time = 1
        self.connect_or_create_all_users()
        self.user_connections = UserConnections(self.connection)

    def test_user_connections_management(self):
        self.list_all_active_user_connections()
        self.disconnect_user_connection()
        self.list_all_active_user_connections()
        self.disconnect_user_connection_on_node()
        self.list_all_active_user_connections()
        self.disconnect_all_user_connections_on_node()
        self.connect_or_create_all_users()
        self.list_all_active_user_connections()
        self.disconnect_all_user_connections()
        self.list_all_active_user_connections()

    def connect_or_create_all_users(self):
        self.user1 = self.connection_configs["user1"]
        self.user2 = self.connection_configs["user2"]
        self.user3 = self.connection_configs["user3"]
        self.user4 = self.connection_configs["user4"]

        user_list = [self.user1, self.user2, self.user3, self.user4]
        existing_users = [u.username for u in list_users(self.connection)]
        for user in user_list:
            if user["name"] not in existing_users:
                User.create(self.connection,
                            username=user["name"],
                            full_name=user["name"],
                            password=user["pass"],
                            require_new_password=False)
            Connection(
                base_url=self.env_url,
                username=user["name"],
                password=user["pass"],
                project_id=None,
                login_mode=self.login_mode,
            )

    def list_all_active_user_connections(self):
        self.all_connections = self.user_connections.list_connections()
        self.all_ids = []
        time.sleep(self.wait_time)
        for item in self.all_connections:
            if item["username"].startswith("con_user"):
                self.all_ids.append(item["id"])

    def disconnect_user_connection(self):
        id_to_drop = self.all_ids[0]
        self.user_connections.disconnect_users([id_to_drop])
        time.sleep(self.wait_time)
        self.list_all_active_user_connections()
        self.assertNotIn(id_to_drop, self.all_ids)

    def disconnect_user_connection_on_node(self):
        id_to_drop = self.all_ids[0]
        self.user_connections.disconnect_users(
            connection_ids=[id_to_drop], nodes=self.env_name
        )
        time.sleep(self.wait_time)
        self.list_all_active_user_connections()
        self.assertNotIn(id_to_drop, self.all_ids)

    def disconnect_all_user_connections_on_node(self):
        id_to_drop = self.all_ids[0]
        self.user_connections.disconnect_users(
            nodes=self.env_name, force=True
        )
        time.sleep(self.wait_time)
        self.list_all_active_user_connections()
        self.assertNotIn(id_to_drop, self.all_ids)

    def disconnect_all_user_connections(self):
        id_to_drop = self.all_ids[0]
        self.user_connections.disconnect_users(force=True)
        time.sleep(self.wait_time)
        self.list_all_active_user_connections()
        self.assertNotIn(id_to_drop, self.all_ids)

    def tearDown(self):
        self.user_connections.disconnect_users(force=True)
        self.connection.close()
