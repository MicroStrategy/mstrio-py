from unittest import TestCase

import stringcase

from mstrio.admin.application import Application
from mstrio.admin.security_role import list_security_roles
from mstrio.admin.user import list_users
from mstrio.admin.usergroup import list_usergroups
from mstrio.admin.privilege import Privilege
from mstrio.admin.user_connections import UserConnections

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestParamNamingConversion(TestCase):
    """Test if REST API response fields are converted correctly to snake_case
    and then back."""

    @classmethod
    def setUpClass(cls):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])
        cls.user_csv_path = config_paths["user_csv"]

        cls.env_url = general_configs["env_url"]
        cls.username = general_configs["username"]
        cls.password = general_configs["password"]
        cls.login_mode = general_configs["login_mode"]
        cls.env_name = general_configs["env_name"]
        cls.project_id = general_configs["project_id"]

        cls.connection = con.get_connection(
            url=cls.env_url,
            username=cls.username,
            password=cls.password,
            login_mode=cls.login_mode,
            project_id=None,
        )

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    # def convert_to_and_from(self, name):
    #     to_snake_case = inflection.underscore(name)
        # to_camel_case = inflection.camelize(to_snake_case, uppercase_first_letter=False)
    #     self.assertEqual(name, to_camel_case)

    # def convert_to_and_from(self, name):
    #     snake_case = helper.camel_to_snake(name)
    #     camel_case = helper.snake_to_camel(snake_case)
    #     self.assertEqual(name, camel_case)

    def convert_to_and_from(self, name):
        camel_case = stringcase.camelcase(name)
        snake_case = stringcase.snakecase(camel_case)
        # print("original: " + name)
        # print("snake: " + snake_case)
        # print("camel: " + camel_case)
        # print("____________________________")
        self.assertEqual(name, snake_case)

    def test_user_attr_conversion(self):
        """Convert User object attributes."""
        self.user = list_users(self.connection, limit=1)[0]
        self.user.fetch()

        for attr in self.user.list_properties().keys():
            with self.subTest(i=attr):
                self.convert_to_and_from(attr)

    def test_usergroup_attr_conversion(self):
        """Convert UserGroup object attributes."""
        self.usergroup = list_usergroups(self.connection, limit=1)[0]
        self.usergroup.fetch()

        for attr in self.usergroup.list_properties().keys():
            with self.subTest(i=attr):
                self.convert_to_and_from(attr)

    def test_application_attr_conversion(self):
        """Convert Application object attributes."""
        # self.application = Application._list_loaded_applications(self.connection, )[0]
        self.application = Application(self.connection, id=self.project_id)

        for attr in self.application.list_properties().keys():
            with self.subTest(i=attr):
                self.convert_to_and_from(attr)

    # def test_application_settings_conversion(self):
    #     """Convert Application Settings object attributes"""
    #     self.application = Application(self.connection, id=self.project_id)

    #     for attr in self.application.settings.list_properties().keys():
    #         with self.subTest(setting=attr):
    #             self.convert_to_and_from(attr)

    def test_privilege_conversion(self):
        """Convert Privilege object attributes."""
        self.privilege = Privilege(self.connection, id=1)

        for attr in self.privilege.list_properties().keys():
            with self.subTest(i=attr):
                self.convert_to_and_from(attr)

    def test_security_roles_conversion(self):
        """Convert Security Role object attributes."""
        self.security_role = list_security_roles(self.connection)[0]

        for attr in self.security_role.list_properties().keys():
            with self.subTest(i=attr):
                self.convert_to_and_from(attr)

    def test_user_connections_conversion(self):
        """Convert user Connections fields."""
        self.user_connections = UserConnections(self.connection).list_connections(limit=1)[0]

        for attr in self.user_connections.keys():
            with self.subTest(i=attr):
                self.convert_to_and_from(attr)
