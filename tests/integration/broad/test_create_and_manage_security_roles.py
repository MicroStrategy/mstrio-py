from unittest import TestCase

from mstrio.admin.privilege import Privilege
from mstrio.admin.security_role import SecurityRole, list_security_roles

from production.tests.integration.resources import mstr_connect as con
from production.tests.integration.resources.commons import read_configs


class TestCreateAndManageSecurityRoles(TestCase):
    """TC67381"""

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

    def test_create_and_manage_security_roles_part1_red(self):
        """This test won't pass as long as server level privileges are not
        supported by REST API."""
        self.create_security_role()
        self.modify_security_role_to_assign_application_level_privileges()
        self.list_all_privileges_with_source_for_a_security_role()
        self.create_another_security_role()
        self.modify_privileges_for_both_security_roles_at_once()
        self.list_all_privileges_with_source_for_both_security_roles()
        self.remove_privileges_for_a_first_security_role_and_list_its_privileges()
        self.delete_first_security_role()
        self.list_all_privileges_with_source_for_the_first_security_role()

    def create_security_role(self):
        privileges = Privilege.list_privileges(self.connection, True)
        self.application_level_privileges = [
            p["id"] for p in privileges if p["is_project_level_privilege"]
        ][-1]
        print(self.application_level_privileges)
        self.server_level_privileges = [
            p["id"] for p in privileges if not p["is_project_level_privilege"]
        ][-1]
        SecurityRole.create(
            self.connection, "integration test role", privileges[0]['id']
        )
        self.security_role = SecurityRole(self.connection, "integration test role")

    def modify_security_role_to_assign_application_level_privileges(self):
        self.security_role.revoke_all_privileges(force=True)
        self.security_role.grant_privilege(self.application_level_privileges)
        self.assertEqual(
            [self.application_level_privileges],
            [p['id'] for p in self.security_role.privileges],
        )

    def list_all_privileges_with_source_for_a_security_role(self):
        role_privileges = self.security_role.privileges
        self.assertGreater(len(role_privileges), 0)

    def modify_security_role_to_assign_server_level_privileges(self):
        self.security_role.revoke_all_privileges(force=True)
        self.security_role.grant_privilege(self.server_level_privileges)
        self.assertEqual(
            [self.server_level_privileges],
            [p['id'] for p in self.security_role.privileges],
        )

    def create_another_security_role(self):
        privileges = Privilege.list_privileges(self.connection, True)
        self.application_level_privileges = [
            p["id"] for p in privileges if p["is_project_level_privilege"]
        ][-1]
        print(self.application_level_privileges)
        self.server_level_privileges = [
            p["id"] for p in privileges if not p["is_project_level_privilege"]
        ][-1]
        SecurityRole.create(
            self.connection, "integration test role 2", privileges[0]['id']
        )
        self.new_security_role = SecurityRole(self.connection, "integration test role 2")

    def modify_privileges_for_both_security_roles_at_once(self):
        self.security_role.revoke_all_privileges(force=True)
        self.new_security_role.revoke_all_privileges(force=True)
        self.security_role.grant_privilege(self.application_level_privileges)
        self.new_security_role.grant_privilege(self.application_level_privileges)
        self.assertEqual(
            [self.application_level_privileges],
            [p['id'] for p in self.security_role.privileges],
        )
        self.assertEqual(
            [self.application_level_privileges],
            [p['id'] for p in self.new_security_role.privileges],
        )

    def list_all_privileges_with_source_for_both_security_roles(self):
        role_privileges = self.security_role.privileges + self.new_security_role.privileges
        self.assertGreater(len(role_privileges), 0)

    def remove_privileges_for_a_first_security_role_and_list_its_privileges(self):
        self.security_role.revoke_all_privileges(force=True)
        role_privileges = self.security_role.privileges
        self.assertEqual(len(role_privileges), 0)

    def delete_first_security_role(self):
        security_role_name = self.security_role.name
        self.security_role.delete(force=True)
        self.assertNotIn(security_role_name,
                         [r.name for r in list_security_roles(self.connection)])

    def list_all_privileges_with_source_for_the_first_security_role(self):
        self.assertRaises(Exception, self.security_role.list_privileges)

    def tearDown(self):
        for role in list_security_roles(self.connection):
            if role.name.startswith('integration test role'):
                role.delete(force=True)
        self.connection.close()
