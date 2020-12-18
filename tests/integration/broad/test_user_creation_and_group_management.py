from datetime import datetime
from unittest import TestCase

from mstrio.admin.user import User, list_users
from mstrio.admin.usergroup import UserGroup, list_usergroups

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestUserCreationAndGroupManagement(TestCase):
    """TC67375"""

    def setUp(self):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])

        self.env_url = general_configs["env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["password"]
        self.login_mode = general_configs["login_mode"]

        self.connection = con.get_connection(
            url=self.env_url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id=None,
        )

        self.user1 = None
        self.user2 = None
        self.user_group = None

    def test_user_creation_and_user_group_management(self):
        self.create_user_group()
        self.remove_user_from_the_group_and_get_list_of_users()
        self.add_new_user_to_the_group_modify_and_get_list_of_users()
        self.get_properties_for_user_group()
        self.remove_user_group()

    def create_user_group(self):
        timestamp = datetime.now().strftime("%y_%m_%d_%H_%M_%S_%f")
        self.group_name = "Integration Test User Group {}".format(timestamp)
        self.user_group = UserGroup.create(self.connection, self.group_name)
        self.user1 = User.create(self.connection, "test user1", "test user1")
        self.user2 = User.create(self.connection, "test user2", "test user2")
        self.user_group.add_users([self.user1.id, self.user2.id])
        self.assertIsInstance(self.user_group.id, str)

    def remove_user_from_the_group_and_get_list_of_users(self):
        self.assertIn(self.user1.id, [u["id"] for u in self.user_group.members])
        self.assertIn(self.user2.id, [u["id"] for u in self.user_group.members])
        self.user_group.remove_users([self.user2.id])
        self.user_group.fetch()
        self.assertIn(self.user1.id, [u["id"] for u in self.user_group.members])
        self.assertNotIn(self.user2.id, [u["id"] for u in self.user_group.members])

    def add_new_user_to_the_group_modify_and_get_list_of_users(self):
        new_username2 = "new username"
        old_user_id2 = self.user2.id

        self.assertNotEqual(self.user2.username, new_username2)
        self.assertNotIn(self.user2.id, [u["id"] for u in self.user_group.members])
        self.user_group.add_users([self.user2.id])
        self.user_group.fetch()
        self.user2.username = new_username2
        self.user2.update_properties()
        self.user2.fetch()
        self.assertEqual(self.user2.username, new_username2)
        self.assertEqual(self.user2.id, old_user_id2)
        self.assertIn(self.user2.id, [u["id"] for u in self.user_group.members])

    def get_properties_for_user_group(self):
        info = self.user_group.list_properties()
        self.assertEqual(self.group_name, info["name"])

    def remove_user_group(self):
        self.user_group.delete(force=True)
        self.assertRaises(Exception, self.user_group.fetch)

    def tearDown(self) -> None:
        if self.user1 is None or self.user2 is None:
            users = list_users(self.connection, name_begins='test user')
            for user in users:
                user.delete(force=True)
        else:
            self.user1.delete(force=True)
            self.user2.delete(force=True)

        if self.user_group is None:
            groups = list_usergroups(self.connection, name_begins='Test User Group 20')
            for group in groups:
                group.delete(force=True)
