"""This is the demo script to show how administrator can manage server and the
cluster with its nodes.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.server import Cluster, Environment, Project

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, login_mode=1)
MICROSTRATEGY_TUTORIAL = 'MicroStrategy Tutorial'

# get the cluster for given connection
clstr = Cluster(connection=conn)

# save topologies of services or nodes from this cluster into a dataframe
nodes_topology_df = clstr.nodes_topology()
services_topology_df = clstr.services_topology()

# get list of services grouped by nodes or by services
services_by_nodes = clstr.list_services(group_by='nodes')
services_by_services = clstr.list_services(group_by='services')

# get list of nodes (information about projects within each node is given there)
nodes = clstr.list_nodes(to_dictionary=True)
# remove/add a node from/to a cluster (node with the given name should exist)
clstr.remove_node(name='env-xxxxxxlaio3use1')
clstr.add_node(name='env-xxxxxxlaio3use1')

# get name of default (primary) node of the cluster and set new default node
clstr.default_node
clstr.set_primary_node(name='env-xxxxxxlaio3use1')

# update node settings or reset them to default values
clstr.update_node_settings(node='env-xxxxxxlaio3use1', load_balance_factor=99,
                           initial_pool_size=511, max_pool_size=1023)
clstr.reset_node_settings(node='env-xxxxxxlaio3use1')

# stop/start service on selected nodes (error will be thrown in case of wrong
# names of service or nodes)
clstr.stop(service='Apache-Kafka', nodes=['env-xxxxxxlaio1use1', 'env-xxxxxxlaio2use1'])
clstr.start(service='Apache-Kafka', nodes=['env-xxxxxxlaio1use1', 'env-xxxxxxlaio2use1'])

env = Environment(connection=conn)
# list all projects available for the given connection (it is possible via
# class Cluster or Environment)
projects = env.list_projects()
projects = clstr.list_projects()

# load or unload chosen project (it is possible via class Cluster or
# Project)
project = Project(connection=conn, name=MICROSTRATEGY_TUTORIAL)
project.load()
project.unload()

# via Cluster can we also specify on which node(s) project will be loaded
# or unloaded
clstr.load_project(project=MICROSTRATEGY_TUTORIAL,
                   on_nodes=['env-xxxxxxlaio1use1', 'env-xxxxxxlaio2use1'])
clstr.unload_project(project=MICROSTRATEGY_TUTORIAL,
                     on_nodes=['env-xxxxxxlaio1use1', 'env-xxxxxxlaio2use1'])

# get settings of a server as a dataframe
server_settings_df = env.server_settings.to_dataframe

# save/load settings of a server to/from a file (format can be 'csv', 'json' or
# 'pickle')
env.server_settings.to_csv(name="server_settings.csv")
env.server_settings.import_from(file="server_settings.csv")

# update some settings of a server
env.server_settings.allowUserLoginWithFullName = True
env.server_settings.minCharsPasswordChanges = 1
env.server_settings.update()
