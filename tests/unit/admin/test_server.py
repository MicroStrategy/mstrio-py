from unittest import TestCase

from mstrio.admin import server
from mstrio import connection
from production.tests.resources.mocks.mock_connection import MockConnection
from production.tests.resources.mocks.mock_cluster import MockCluster

import pandas as pd


class TestServer(TestCase):
    """Test server module functionalities."""

    @classmethod
    def setUpClass(cls):
        connection.projects = MockConnection.mock_projects_api()
        connection.authentication = MockConnection.mock_authentication_api()
        connection.misc = MockConnection.mock_misc_api()

        server.registrations = MockCluster.mock_registrations_api()
        server.administration = MockCluster.mock_administration_api()
        server.monitors = MockCluster.mock_monitors_api()
        cls.nodes = ['env-225486laio1use1', 'env-225486laio2use1']
        cls.connection = connection.Connection(base_url='http://mocked.url.com',
                                               username='username',
                                               password='password')

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def test_init(self):
        cluster = server.Cluster(connection=self.connection)
        self.assertIsInstance(cluster.list_nodes(), list)
        self.assertEqual(len(cluster.list_nodes()), 2)

    def test_nodes_topology(self):
        cluster = server.Cluster(connection=self.connection)
        df = cluster.nodes_topology()
        self.assertIsInstance(df, pd.io.formats.style.Styler)
        self.assertEqual(len(set(df.data['env-225486laio1use1'].tolist())), 3)
        self.assertEqual(len(set(df.data['env-225486laio2use1'].tolist())), 3)

    def test_nodes_topology_no_service_control(self):
        iserver_version_tmp = self.connection.iserver_version
        self.connection.iserver_version = '11.3.0001'
        cluster = server.Cluster(connection=self.connection)
        df = cluster.nodes_topology()
        self.assertIsInstance(df, pd.io.formats.style.Styler)
        self.assertEqual(len(set(df.data['env-225486laio1use1'].tolist())), 3)
        self.assertEqual(len(set(df.data['env-225486laio2use1'].tolist())), 1)
        self.connection.iserver_version = iserver_version_tmp

    def test_services_topology(self):
        cluster = server.Cluster(connection=self.connection)
        df = cluster.services_topology()
        self.assertIsInstance(df, pd.io.formats.style.Styler)

    def test_list_services(self):
        cluster = server.Cluster(connection=self.connection)
        services = cluster.list_services(group_by='services')
        self.assertIsInstance(services, list)
        self.assertEqual(len(services), 17)
        nodes = cluster.list_services(group_by='nodes')
        self.assertIsInstance(nodes, list)
        self.assertEqual(len(nodes), 2)

    def test_list_node_settings(self):
        cluster = server.Cluster(connection=self.connection)
        node_settings = cluster.list_node_settings('Apache-Kafka')
        self.assertIsInstance(node_settings, dict)
        self.assertEqual(node_settings['initialPoolSize'], 10)
        self.assertEqual(node_settings['maxPoolSize'], 100)

    def test_add_node(self):
        cluster = server.Cluster(connection=self.connection)
        cluster.add_node('env-225486laio1use1')

    def test_remove_node(self):
        cluster = server.Cluster(connection=self.connection)
        cluster.remove_node('env-225486laio1use1')

    def test_start_service(self):
        cluster = server.Cluster(connection=self.connection)
        cluster.start(service='Apache-Kafka', nodes=['env-225486laio1use1'], login='login', passwd='passwd')

    def test_stop_service(self):
        cluster = server.Cluster(connection=self.connection)
        cluster.stop(service='Apache-Kafka', nodes=['env-225486laio2use1'], login='login', passwd='passwd', force=True)

    def test_reset_node_settings(self):
        cluster = server.Cluster(connection=self.connection)
        cluster.reset_node_settings(node='env-225486laio1use1')
