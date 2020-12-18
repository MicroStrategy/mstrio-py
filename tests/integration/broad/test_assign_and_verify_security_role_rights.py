from unittest import TestCase

import requests
from mstrio.admin.security_role import SecurityRole, list_security_roles
from mstrio.admin.user import User, list_users
from mstrio.report import Report

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestAssignAndVerifySecurityRoleRights(TestCase):
    """TC67904"""

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
        self.project_name = general_configs["project_name"]
        self.report_id = general_configs["report_id"]

        self.connection = con.get_connection(url=self.env_url,
                                             username=self.username,
                                             password=self.password,
                                             login_mode=self.login_mode,
                                             project_id=self.project_id)
        self.user_connection = None

    def test_assign_and_verify_security_role_rights(self):
        self.create_security_role_and_assign_users()
        self.deny_read_permissions()
        self.login_to_env_with_a_user_from_security_role()
        self.check_access_to_report()

    def create_security_role_and_assign_users(self):
        security_roles = list_security_roles(self.connection)
        security_roles[0]
        privileges = [p['id'] for p in security_roles[0].privileges]
        self.security_role = SecurityRole.create(self.connection,
                                                 'integration test role TC67904',
                                                 privileges)
        self.user = User.create(self.connection,
                                username='test_user1',
                                full_name='integration test user1 TC67904',
                                password='mstr123',
                                require_new_password=False)
        self.security_role.grant_to([self.user.id], self.project_name)
        for user_kwargs in self.security_role.list_members():
            user = User(self.connection, id=user_kwargs['id'])
            user.set_custom_permissions(execute='grant', to_objects=[self.report_id], object_type=3)
            connection = con.get_connection(url=self.env_url,
                                            username=user.username,
                                            password='mstr123',
                                            login_mode=self.login_mode,
                                            project_id=self.project_id)
            report = Report(connection, report_id=self.report_id)
            report.to_dataframe()
            connection.close()

    def deny_read_permissions(self):
        for user_kwargs in self.security_role.list_members():
            user = User(self.connection, id=user_kwargs['id'])
            user.set_custom_permissions(execute='deny', to_objects=[self.report_id], object_type=3)

    def login_to_env_with_a_user_from_security_role(self):
        self.user_connection = con.get_connection(url=self.env_url,
                                                  username='test_user1',
                                                  password='mstr123',
                                                  login_mode=self.login_mode,
                                                  project_id=self.project_id)

    def check_access_to_report(self):
        report = Report(self.user_connection,
                        report_id=self.report_id)
        with self.assertRaises(requests.exceptions.HTTPError):
            report.to_dataframe()

    def tearDown(self):

        for role in list_security_roles(self.connection):
            if role.name.startswith('integration test'):
                role.delete(force=True)
        for user in list_users(self.connection, name_begins='integration test'):
            if user.name.startswith('integration test'):
                user.delete(force=True)

        self.connection.close()
        self.user_connection.close()
