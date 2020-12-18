from unittest import TestCase

from mstrio.admin.dataset import Dataset, list_datasets
from mstrio.admin.document import Document, list_documents
from mstrio.admin.dossier import Dossier, list_dossiers

from ..resources import mstr_connect as con
from ..resources.commons import read_configs


class TestManageVLDBProperties(TestCase):
    def setUp(self):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])
        url = general_configs["env_url"]
        usr = general_configs["username"]
        pwd = general_configs["password"]
        mode = general_configs["login_mode"]
        self.pid = general_configs["project_id"]
        self.names = [
            "Join Across Datasets",
            "Join Across Datasets",
            "Max Tables in Join Warning",
        ]
        self.conn = con.get_connection(url, usr, pwd, self.pid, mode)
        documents = list_documents(self.conn)
        dossiers = list_dossiers(self.conn, to_dictionary=False)
        datasets = list_datasets(self.conn)
        self.objects = [
            Document(self.conn, id=documents[0].id),
            Dossier(self.conn, id=dossiers[0].id),
            Dataset(self.conn, id=datasets[0].id),
        ]

    def tearDown(self):
        self.conn.close()

    def test_manage_vldb_properties(self):
        """TC70128"""
        for obj, name in zip(self.objects, self.names):
            previous_state = obj.list_vldb_settings()
            obj.alter_vldb_settings("VLDB Select", name, 23, self.pid)
            current_state = obj.list_vldb_settings()
            self.assertNotEqual(previous_state, current_state)
            obj.reset_vldb_settings()
