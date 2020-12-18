from unittest import TestCase

from mstrio.admin import usergroup
from mstrio import connection

from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_entity import MockEntity
from production.tests.resources.mocks.mock_usergroup import MockUsergroup
from production.tests.resources.mocks.mock_security import MockSecurity


class TestUserGroup(TestCase):
    test_df_path = 'production/tests/resources/api-responses/admin/user/user.csv'

    def setUp(self):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        from mstrio.utils import entity
        entity.objects = MockEntity.mock_objects()

        from mstrio.admin import privilege
        privilege.security = MockSecurity.mock_security_api()

        usergroup.usergroups = MockUsergroup.mock_usergroups_api()
        usergroup.UserGroup._API_GETTERS = {
            None: usergroup.usergroups.get_user_group_info,
            # 'memberships': usergroup.usergroups.get_memberships,
            # 'members': usergroup.usergroups.get_members,
            # 'security_roles': usergroup.usergroups.get_security_roles,
            'privileges': usergroup.usergroups.get_privileges,
            'settings': usergroup.usergroups.get_settings
        }
        usergroup.UserGroup._API_PATCH = [usergroup.usergroups.update_user_group_info]

        self.connection = connection.Connection(base_url='http://mocked.url.com',
                                                username='username',
                                                password='password')

        self.connection2 = connection.Connection(base_url='http://mocked2.url.com',
                                                 username='username2',
                                                 password='password2')

    def test_get_usergroups(self):
        usrgroups = usergroup.list_usergroups(self.connection)
        self.assertIsInstance(usrgroups, list)
        self.assertIsInstance(usrgroups[0], usergroup.UserGroup)
        self.assertEqual(len(usrgroups), 21)
        self.assertEqual(usrgroups[1].name, 'AnalyticsServer')

        usrgroups = usergroup.list_usergroups(self.connection, to_dictionary=True)
        self.assertIsInstance(usrgroups, list)
        self.assertIsInstance(usrgroups[0], dict)
        self.assertEqual(len(usrgroups), 21)
        self.assertEqual(usrgroups[1]['id'], '98AA5CA04DD6D20C6875C6B314874A1C')

    def test_init(self):
        usrgroup_id = '23FBA9B611EAD7D516E20080EF651034'
        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)
        self.assertEqual(usrgroup.name, 'tmp_unit_test_user_group_1')

    def test_create(self):
        usrgroup = usergroup.UserGroup.create(connection=self.connection, name='tmp_unit_test_user_group_1')
        self.assertEqual(usrgroup.name, 'tmp_unit_test_user_group_1')

    def test_delete(self):
        usrgroup_id = '23FBA9B611EAD7D516E20080EF651034'
        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)
        is_deleted = usrgroup.delete(force=True)
        self.assertTrue(is_deleted)

    def test_add_users(self):
        usrgroup_id = '23FBA9B611EAD7D516E20080EF651034'
        member_id_1 = 'E96A7C6611D4BBCE10004694316DE8A4'
        member_id_2 = '6DA105CF11EAD31783510080EF65A0DF'

        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)

        self.assertFalse(self.checkMember(member_id_1, usrgroup.members))
        self.assertFalse(self.checkMember(member_id_2, usrgroup.members))
        self.assertEqual(len(usrgroup.members), 0)

        usrgroup.add_users([member_id_1, member_id_2])

        self.assertTrue(self.checkMember(member_id_1, usrgroup.members))
        self.assertTrue(self.checkMember(member_id_2, usrgroup.members))
        self.assertEqual(len(usrgroup.members), 2)

    def test_remove_users(self):
        usrgroup_id = 'D09773F94699124B4D75B48F1B358327'
        member_id_1 = 'E96A7C6611D4BBCE10004694316DE8A4'
        member_id_2 = '6DA105CF11EAD31783510080EF65A0DF'

        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)

        self.assertTrue(self.checkMember(member_id_1, usrgroup.members))
        self.assertTrue(self.checkMember(member_id_2, usrgroup.members))
        self.assertEqual(len(usrgroup.members), 2)

        usrgroup.remove_users([member_id_2])

        self.assertTrue(self.checkMember(member_id_1, usrgroup.members))
        self.assertFalse(self.checkMember(member_id_2, usrgroup.members))
        self.assertEqual(len(usrgroup.members), 1)

    def test_remove_all_users(self):
        usrgroup_id = '98AA5CA04DD6D20C6875C6B314874A1C'
        member_id_1 = 'E96A7C6611D4BBCE10004694316DE8A4'
        member_id_2 = '6DA105CF11EAD31783510080EF65A0DF'

        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)

        self.assertTrue(self.checkMember(member_id_1, usrgroup.members))
        self.assertTrue(self.checkMember(member_id_2, usrgroup.members))
        self.assertEqual(len(usrgroup.members), 2)

        usrgroup.remove_all_users()

        self.assertFalse(self.checkMember(member_id_1, usrgroup.members))
        self.assertFalse(self.checkMember(member_id_2, usrgroup.members))
        self.assertEqual(len(usrgroup.members), 0)

    def test_add_to_usergroups(self):
        usrgroup_id = '23FBA9B611EAD7D516E20080EF651034'
        membership_id1 = '3D0F5EF8978D4AE086012C196BF01EBA'
        membership_id2 = '5B9C0CCF4530F8F0CFD93DA84B96F997'
        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)

        self.assertFalse(self.checkMembership(membership_id1, usrgroup.memberships))
        self.assertFalse(self.checkMembership(membership_id2, usrgroup.memberships))
        self.assertEqual(len(usrgroup.memberships), 0)

        usrgroup.add_to_usergroups([membership_id1, membership_id2])

        self.assertTrue(self.checkMembership(membership_id1, usrgroup.memberships))
        self.assertTrue(self.checkMembership(membership_id2, usrgroup.memberships))
        self.assertEqual(len(usrgroup.memberships), 2)

    def test_remove_from_usergroups(self):
        usrgroup_id = 'E87FB53F46A623DA07C323A420DB1B49'
        membership_id1 = '3D0F5EF8978D4AE086012C196BF01EBA'
        membership_id2 = '5B9C0CCF4530F8F0CFD93DA84B96F997'

        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)

        self.assertTrue(self.checkMembership(membership_id1, usrgroup.memberships))
        self.assertTrue(self.checkMembership(membership_id2, usrgroup.memberships))
        self.assertEqual(len(usrgroup.memberships), 2)

        usrgroup.remove_from_usergroups([membership_id1])

        self.assertFalse(self.checkMembership(membership_id1, usrgroup.memberships))
        self.assertTrue(self.checkMembership(membership_id2, usrgroup.memberships))
        self.assertEqual(len(usrgroup.memberships), 1)

    def test_grant_privilege(self):
        usrgroup_id = '23FBA9B611EAD7D516E20080EF651034'
        privilege_id_1 = '146'
        privilege_id_2 = '150'

        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)

        usrgroup.grant_privilege(privilege=[privilege_id_1, privilege_id_2])

        self.assertTrue(self.checkPrivilege(privilege_id_1, usrgroup.privileges))
        self.assertTrue(self.checkPrivilege(privilege_id_2, usrgroup.privileges))
        self.assertEqual(len(usrgroup.privileges), 2)

    def test_revoke_privilege(self):
        usrgroup_id = 'A51EE17B415A313F78DF4998743C4CCC'
        privilege_id_1 = '146'
        privilege_id_2 = '150'

        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)

        usrgroup.revoke_privilege(privilege=privilege_id_2)

        self.assertTrue(self.checkPrivilege(privilege_id_1, usrgroup.privileges))
        self.assertFalse(self.checkPrivilege(privilege_id_2, usrgroup.privileges))
        self.assertEqual(len(usrgroup.privileges), 1)

    def checkMember(self, id, members):
        for m in members:
            if m['id'] == id:
                return True
        return False

    def checkMembership(self, id, memberships):
        for m in memberships:
            if m['id'] == id:
                return True
        return False

    def checkPrivilege(self, id, privileges):
        for p in privileges:
            if p['privilege']['id'] == id:
                return True
        return False

    def test_get_settings(self):
        usrgroup_id = '23FBA9B611EAD7D516E20080EF651034'
        usrgroup = usergroup.UserGroup(connection=self.connection, id=usrgroup_id)

        settings = usrgroup.get_settings()
        self.assertEqual(settings['jobMemGoverning']['value'], 0)
        self.assertEqual(settings['jobMemGoverning']['effectiveValue'], 4611686018427387904)
