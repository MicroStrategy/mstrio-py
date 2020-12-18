from unittest import TestCase

from mstrio.admin.dossier import Dossier
from mstrio.admin.usergroup import UserGroup
from mstrio.library import Library

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestManagingUserLibraries(TestCase):
    def setUp(self):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        self.confs = read_configs(config_paths["general_configs"])
        url = self.confs["env_url"]
        pid = self.confs["project_id"]
        mode = self.confs["login_mode"]
        self.dossier_id = "0D0CDC8F11E97E8F00000080AFB3A407"
        self.user1_conn = con.get_connection(
            url, self.confs["username"], self.confs["password"], pid, mode
        )
        self.user2_conn = con.get_connection(
            url, self.confs["username2"], self.confs["password2"], pid, mode
        )
        self.user1_group_dossier = Dossier(self.user1_conn, id=self.dossier_id)

        try:
            self.user1_group = UserGroup(self.user1_conn, "test")
        except ValueError:
            self.user1_group = UserGroup.create(self.user1_conn,
                                                name='test',
                                                members=[self.user1_conn.user_id, self.user2_conn.user_id])
            self.user1_group_dossier.publish(self.user1_group)

        self.user1_library = Library(self.user1_conn)
        self.user2_library = Library(self.user2_conn)

    def tearDown(self):
        self.user1_conn.close()
        self.user2_conn.close()

    def test_managing_user_libraries(self):
        """TC69914"""
        self.check_dossier_in(self.user1_library, self.user2_library)
        self.user1_library.unpublish(self.dossier_id)
        self.check_dossier_not_in(self.user1_library)
        self.check_dossier_in(self.user2_library)

        self.user1_library.publish(self.dossier_id)
        self.check_dossier_in(self.user1_library, self.user2_library)

        self.user1_group_dossier.unpublish(self.user1_group)
        self.check_dossier_not_in(self.user1_library, self.user2_library)

        self.user1_group_dossier.publish(self.user1_group)
        self.check_dossier_in(self.user1_library, self.user2_library)

    def check_dossier_in(self, *libs):
        for lib in libs:
            dossier_state = lib.dossiers
            dossier_ids = [dossier.id for dossier in dossier_state]
            self.assertIn(self.dossier_id, dossier_ids)

    def check_dossier_not_in(self, *libs):
        for lib in libs:
            dossier_state = lib.dossiers
            dossier_ids = [dossier.id for dossier in dossier_state]
            self.assertNotIn(self.dossier_id, dossier_ids)
