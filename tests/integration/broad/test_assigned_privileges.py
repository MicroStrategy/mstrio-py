import time
from unittest import TestCase

from mstrio.admin.application import Environment, Application
from mstrio.admin.privilege import Privilege
from mstrio.admin.security_role import SecurityRole, list_security_roles
from mstrio.admin.user import User, UserConnections, list_users
from mstrio.connection import Connection

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestAssignedPrivileges(TestCase):
    """TC67382"""

    def setUp(self):
        config_paths = read_configs('production/tests/integration/resources/config_paths.json')
        general_configs = read_configs(config_paths['general_configs'])
        self.user_csv_path = config_paths['user_csv']

        self.env_url = general_configs["env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["password"]
        self.login_mode = general_configs["login_mode"]
        self.env_name = general_configs["env_name"]
        self.project_id = general_configs["project_id"]
        self.report_id = general_configs["report_id"]

        self.connection = Connection(base_url=self.env_url,
                                     username=self.username,
                                     password=self.password,
                                     login_mode=self.login_mode,
                                     project_id=self.project_id)

    def test_assigned_privileges(self):
        self.create_security_role_with_new_user()
        self.modify_privileges_and_verify_access()

    def create_security_role_with_new_user(self):
        self.user = User.create(self.connection,
                                username='integration_test_usr',
                                password='',
                                full_name='TC67382 test user')
        self.user.revoke_all_privileges(force=True)
        self.old_privileges = Privilege.list_privileges(self.connection)
        self.old_privileges = [p.id for p in self.old_privileges if p.is_project_level_privilege][:1]
        self.new_privileges = Privilege.list_privileges(self.connection)
        self.new_privileges = [p.id for p in self.new_privileges if p.is_project_level_privilege][1:2]
        self.security_role = SecurityRole.create(self.connection,
                                                 name='integration_test_role',
                                                 privileges=self.old_privileges)
        application = Application(self.connection,
                                  id=self.connection.project_id)
        self.user.assign_security_role(self.security_role,
                                       application=application)

    def modify_privileges_and_verify_access(self):
        self.security_role.revoke_all_privileges(force=True)
        self.security_role.grant_privilege(self.new_privileges)
        verification_user = User(self.connection, name=self.user.name)
        verification_privs = verification_user.list_privileges()
        verification_privs = [p['privilege']['id'] for p in verification_privs]
        self.assertIn(self.new_privileges[0],
                      verification_privs)
        self.assertNotIn(self.old_privileges[0],
                         verification_privs)

    def tearDown(self):
        for user in list_users(self.connection, name_begins='TC67382'):
            user.delete(force=True)
        for role in list_security_roles(self.connection,
                                        name='integration_test_role'):
            role.delete(force=True)
