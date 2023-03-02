"""This is the demo script to show how administrator can manage server and the
cluster with its nodes.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.server import Cluster, Environment, Project

from mstrio.connection import get_connection
from mstrio.utils.wip import module_wip, WipLevels

# For some methods to work, a connection to environment
# using user's credentials is needed.
module_wip(globals(), level=WipLevels.WARNING)

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Project to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# get the cluster for given connection
clstr = Cluster(connection=conn)

# save topologies of services or nodes from this cluster into a dataframe
nodes_topology_df = clstr.nodes_topology()
services_topology_df = clstr.services_topology()

# get list of services grouped by nodes or by services
services_by_nodes = clstr.list_services(group_by='nodes')
services_by_services = clstr.list_services(group_by='services')

# Define variables which can be used in a script
NODE_NAME = $node_name
NODE_NAME_2 = $node_name_2

# get list of nodes (information about projects within each node is given there)
nodes = clstr.list_nodes(to_dictionary=True)
# remove/add a node from/to a cluster (node with the given name should exist)
clstr.remove_node(node=NODE_NAME)
clstr.add_node(node=NODE_NAME)

# get name of default (primary) node of the cluster and set new default node
clstr.default_node
clstr.set_primary_node(node=NODE_NAME)

# update node settings or reset them to default values
clstr.update_node_settings(
    node=NODE_NAME, load_balance_factor=99, initial_pool_size=511, max_pool_size=1023
)
clstr.reset_node_settings(node=NODE_NAME)

# Define a variable which can be later used in a script
SERVICE_NAME = $service_name

# stop/start service on selected nodes (error will be thrown in case of wrong
# names of service or nodes)
clstr.stop(service=SERVICE_NAME, nodes=[NODE_NAME, NODE_NAME_2])
clstr.start(service=SERVICE_NAME, nodes=[NODE_NAME, NODE_NAME_2])

# list all projects available for the given connection (it is possible via
# class Cluster or Environment)
env = Environment(connection=conn)
projects = env.list_projects()
projects = clstr.list_projects()

# load or unload chosen project (it is possible via class Cluster or
# Project)
project = Project(connection=conn, name=PROJECT_NAME)
project.load()
project.unload()

# via Cluster can we also specify on which node(s) project will be loaded
# or unloaded
clstr.load_project(project=PROJECT_NAME, on_nodes=[NODE_NAME, NODE_NAME_2])
clstr.unload_project(project=PROJECT_NAME, on_nodes=[NODE_NAME, NODE_NAME_2])

# get settings of a server as a dataframe
server_settings_df = env.server_settings.to_dataframe

# Define a variable which can be later used in a script
FILE_NAME = $file_name  # file name with extension 'csv', 'json' or 'pickle'

# save/load settings of a server to/from a file (format can be 'csv', 'json' or
# 'pickle')
env.server_settings.to_csv(name=FILE_NAME)
env.server_settings.import_from(file=FILE_NAME)

# update some settings of a server
env.server_settings.allowUserLoginWithFullName = True
env.server_settings.minCharsPasswordChanges = 1
env.server_settings.update()
