from unittest import TestCase

from mstrio.admin import user, security_role, user_connections
from mstrio import connection
from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_entity import MockEntity
from production.tests.resources.mocks.mock_user import MockUser
from production.tests.resources.mocks.mock_role import MockRole
from production.tests.resources.mocks.mock_application import MockApplication
from production.tests.resources.mocks.mock_security import MockSecurity
from production.tests.resources.mocks.mock_cluster import MockCluster


class TestUser(TestCase):
    test_df_path = 'production/tests/resources/api-responses/admin/user/user.csv'

    def setUp(self):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        from mstrio.utils import entity
        entity.objects = MockEntity.mock_objects()

        from mstrio.admin import user
        user.users = MockUser.mock_users_api()
        user.objects = MockUser.mock_objects_api()

        from mstrio.admin import security_role
        security_role.security = MockRole.mock_security_api()

        from mstrio.admin import application
        application.monitors = MockApplication.mock_monitors_api()

        from mstrio.admin import user_connections
        user_connections.monitors = MockApplication.mock_monitors_api()

        from mstrio.admin import server
        server.monitors = MockCluster.mock_monitors_api()

        from mstrio.admin import privilege
        privilege.security = MockSecurity.mock_security_api()

        user.User._API_GETTERS = {None: user.users.get_user_info,
                                  'privileges': user.users.get_user_privileges}

        user.User._API_PATCH = [user.users.update_user_info]

        security_role.SecurityRole._API_GETTERS = {None: security_role.security.get_security_role}

        self.connection = connection.Connection(base_url='http://mocked.url.com',
                                                username='username',
                                                password='password')

        self.connection2 = connection.Connection(base_url='http://mocked2.url.com',
                                                 username='username2',
                                                 password='password2')

    def test_create(self):
        u = user.User.create(self.connection,
                             username='test_username',
                             full_name='abc')
        self.assertIsInstance(u, user.User)

    # def test_acl(self):
    #     u = user.User.create(self.connection,
    #                          username='test_username',
    #                          full_name='abc')

    #     obj = user.User.create(self.connection,
    #                            username='test_username',
    #                            full_name='abc')

    #     obj.update_acl(op='REPLACE', rights=0, ids=[u.id])
    #     obj.update_acl_add(rights=20, ids=[u.id])
    #     obj.update_acl_remove(rights=10, ids=[u.id])
    #     obj.update_acl_replace(rights=0, ids=[u.id])

    #     u.set_custom_permissions(browse='grant', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(execute='grant', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(read='grant', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(write='grant', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(control='grant', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(delete='grant', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(use='grant', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(browse='deny', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(execute='deny', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(read='deny', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(write='deny', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(control='deny', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(delete='deny', to_objects=[obj.id], object_type=34)
    #     u.set_custom_permissions(use='deny', to_objects=[obj.id], object_type=34)

    def test_get_users(self):
        users = user.User._get_users(self.connection)
        self.assertIsInstance(users, list)
        self.assertIsInstance(users[0], user.User)

        users = user.User._get_users(self.connection, to_dictionary=True)
        self.assertIsInstance(users, list)
        self.assertIsInstance(users[0], dict)

    def test_create_users_from_csv(self):
        user.User._create_users_from_csv(self.connection, self.test_df_path)

    def test_delete(self):
        u = user.User.create(self.connection,
                             username='test_username',
                             full_name='abc')
        is_deleted = u.delete(force=True)
        self.assertTrue(is_deleted)

    def test_add_address(self):
        u = user.User.create(self.connection,
                             username='test_username',
                             full_name='abc')
        u.add_address(name="some_tmp_address_for_unit_test",
                      address="tmp@microstrategy.com")
        addresses = u.addresses

        self.assertIsInstance(addresses, list)
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0]['name'], 'some_tmp_address_for_unit_test')
        self.assertTrue(addresses[0]['isDefault'])
        with self.assertRaises(ValueError):
            u.add_address(name="some_tmp_address_for_unit_test",
                          address="tmpcom")
        with self.assertRaises(TypeError):
            u.add_address(name="some_tmp_address_for_unit_test",
                          address=2234)

    def test_add_to_usergroups(self):
        u = user.User(self.connection, id='6DA105CF11EAD31783510080EF65A0DF')
        mobile_group = '6B5E4DA24A107AADDEAA02B3AEE76165'
        best_group = '13CB0E1411EAB477376A0080EFC5DACF'
        u.add_to_usergroups([mobile_group, best_group])
        self.assertEqual(len(u.memberships), 3)
        self.assertEqual(u.memberships[0]['id'], best_group)
        self.assertEqual(u.memberships[2]['id'], mobile_group)

    def test_remove_from_usergroups(self):
        u = user.User(self.connection, id='6DA105CF11EAD31783510080EF65A0DF')
        administrator_group = 'E96685CD4E60068559F7DFAC7C2AA851'
        everyone_group = 'C82C6B1011D2894CC0009D9F29718E4F'
        u.remove_from_usergroups([administrator_group])
        self.assertEqual(len(u.memberships), 1)
        self.assertEqual(u.memberships[0]['id'], everyone_group)

    def test_remove_from_all_usergroups(self):
        u = user.User(self.connection, id='6DA105CF11EAD31783510080EF65A0DF')
        u.remove_from_all_usergroups()
        self.assertEqual(len(u.memberships), 0)

    def test_assign_security_role(self):
        user_id = '6DA105CF11EAD31783510080EF65A0DF'
        role_id = '73F7482111D3596C60001B8F67019608'
        # role_id = '12BE6FF211EAC822EDF80080EF25C735'
        project_id = 'B7CA92F04B9FAE8D941C3E9B7E0CD754'
        project_name = 'MicroStrategy Tutorial'

        u = user.User(self.connection, id=user_id)
        sr = security_role.SecurityRole(self.connection, id=role_id)
        u.assign_security_role(sr, application=project_name)

        self.assertTrue(self.check_user_in_securityrole(sr, project_id, user_id))

    def test_revoke_security_role(self):
        user_id = '6DA105CF11EAD31783510080EF65A0DF'
        role_id = '73F7482111D3596C60001B8F67019608'
        role_id = '12BE6FF211EAC822EDF80080EF25C735'
        project_id = 'B7CA92F04B9FAE8D941C3E9B7E0CD754'
        project_name = 'MicroStrategy Tutorial'

        u = user.User(self.connection, id=user_id)
        sr = security_role.SecurityRole(self.connection, id=role_id)
        u.revoke_security_role(sr, application=project_name)

        self.assertFalse(self.check_user_in_securityrole(sr, project_id, user_id))

    def check_user_in_securityrole(self, security_role, project_id, user_id):
        project = None
        for p in security_role.projects:
            if p['id'] == project_id:
                project = p
        if not project:
            return False

        for m in project['members']:
            if m['id'] == user_id:
                return True
        return False

    def test_grant_privilege(self):
        user_id = '6DA105CF11EAD31783510080EF65A0DF'
        u = user.User(self.connection, id=user_id)
        u.grant_privilege(privilege=['64', '65'])
        self.assertEqual(len(u.privileges), 2)
        self.assertTrue(self.check_privilege(u.privileges, '64'))
        self.assertTrue(self.check_privilege(u.privileges, '65'))

    def test_revoke_privilege(self):
        user_id = '157BE23D11EAD31883510080EFB53FDD'
        u = user.User(self.connection, id=user_id)
        u.revoke_privilege(privilege=['64', '65'])
        self.assertFalse(self.check_privilege(u.privileges, '64'))
        self.assertFalse(self.check_privilege(u.privileges, '65'))
        self.assertEqual(len(u.privileges), 0)

    def check_privilege(self, privileges, privilege_id):
        for p in privileges:
            if p['privilege']['id'] == privilege_id:
                return True
        return False

    def test_disconnect(self):
        user_id = '6DA105CF11EAD31783510080EF65A0DF'
        u = user.User(self.connection2, id=user_id)
        u.disconnect()
        connections = user_connections.UserConnections(self.connection2).list_connections()
        self.assertEqual(len(connections), 20)
        self.assertFalse(self.check_user_connection(connections=connections, username='tmp_unit_test_user_1'))

    def test_list_connections(self):
        connections = user_connections.UserConnections(self.connection).list_connections()
        self.assertEqual(len(connections), 22)
        self.assertTrue(self.check_user_connection(connections=connections, username='tmp_unit_test_user_1'))

    def test_disconnect_users(self):
        user_connections.UserConnections(connection=self.connection2).disconnect_users(username='tmp_unit_test_user_1')
        connections = user_connections.UserConnections(self.connection2).list_connections()
        self.assertEqual(len(connections), 20)
        self.assertFalse(self.check_user_connection(connections=connections, username='tmp_unit_test_user_1'))

    def check_user_connection(self, connections, username):
        for uc in connections:
            if (uc['username'] == username):
                return True
        return False
