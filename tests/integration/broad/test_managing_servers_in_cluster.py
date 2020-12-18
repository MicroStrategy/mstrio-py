from unittest import TestCase

from mstrio.admin.server import Cluster

from production.tests.integration.resources import mstr_connect as con
from production.tests.integration.resources.commons import read_configs


class TestManagingServersInCluster(TestCase):
    """TC69904"""

    def setUp(self):
        config_paths = read_configs(
            "production/tests/integration/resources/config_paths.json"
        )
        general_configs = read_configs(config_paths["general_configs"])
        self.env_name1 = general_configs["two_node_env_name1"]
        self.env_name2 = general_configs["two_node_env_name2"]
        self.env_url = general_configs["two_node_env_url"]
        self.username = general_configs["username"]
        self.password = general_configs["two_node_password"]
        self.login_mode = general_configs["login_mode"]
        self.connection = con.get_connection(
            url=self.env_url,
            username=self.username,
            password=self.password,
            login_mode=self.login_mode,
            project_id="B7CA92F04B9FAE8D941C3E9B7E0CD754",
        )
        self.cluster = Cluster(connection=self.connection)

        # check initial cluster nodes
        node_names = [n['name'] for n in self.cluster.list_nodes()]
        if self.env_name1 not in node_names:
            self.add_node_and_check()

    def tearDown(self):
        self.connection.close()

    def test_managing_servers_in_cluster(self):
        self.remove_node_and_check()
        self.add_node_and_check()
        self.assertEqual(self.env_name2, self.cluster.default_node)
        self.cluster.set_primary_node(name=self.env_name1)
        self.assertEqual(self.env_name1, self.cluster.default_node)
        self.cluster.set_primary_node(name=self.env_name2)
        self.assertEqual(self.env_name2, self.cluster.default_node)
        default_settings = {'loadBalanceFactor': 1, 'initialPoolSize': 10, 'maxPoolSize': 100}
        new_settings = {'loadBalanceFactor': 2, 'initialPoolSize': 100, 'maxPoolSize': 1000}
        self.cluster.update_node_settings(self.env_name1, load_balance_factor=2, initial_pool_size=100, max_pool_size=1000)
        self.assertEqual(self.cluster.list_node_settings(self.env_name1), new_settings)
        self.cluster.reset_node_settings(self.env_name1)
        self.assertEqual(self.cluster.list_node_settings(self.env_name1), default_settings)

    def add_node_and_check(self):
        self.cluster.add_node(name=self.env_name1)
        node_names = [n['name'] for n in self.cluster.list_nodes()]
        self.assertIn(self.env_name1, node_names)

    def remove_node_and_check(self):
        self.cluster.remove_node(name=self.env_name1)
        node_names = [n['name'] for n in self.cluster.list_nodes()]
        self.assertNotIn(self.env_name1, node_names)
