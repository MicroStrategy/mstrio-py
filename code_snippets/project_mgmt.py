"""This is the demo script to show how administrator can manage projects
and its settings.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""
from mstrio.datasources import DatasourceInstance
from mstrio.server import compare_project_settings, Environment, Project
from mstrio.connection import get_connection
from mstrio.server.setting_types import FailedEmailDelivery

# Define a variable which can be later used in a script
PROJECT_NAME = $project_name  # Insert name of project to interact with

conn = get_connection(workstationData, project_name=PROJECT_NAME)
env = Environment(connection=conn)

# get list of all projects or those just loaded
all_projects = env.list_projects()
loaded_projects = env.list_loaded_projects()

# get project with a given name
project = Project(connection=conn, name=PROJECT_NAME)

# get nodes from the project
nodes = project.nodes

# Define a variable which can be later used in a script
NODE_NAME = $node_name  # Insert name of node, which is in a project, to load or unload it

# idle/resume a project on a given node(s) (name(s) of existing node(s)
# should be used)
project.idle(on_nodes=[NODE_NAME])
project.resume(on_nodes=NODE_NAME)
# unload/load a project from/to a given node(s) (name(s) of existing
# node(s) should be used)
project.unload(on_nodes=NODE_NAME)
project.load(on_nodes=NODE_NAME)

# get settings of a project as a dataframe
project_settings_df = project.settings.to_dataframe()

# Define variables which can be later used in a script
PROJECT_DESCRIPTION = $project_description  # Insert description of newly created project
PROJECT_NEW_DESCRIPTION = $project_new_description

# create a project and store it in variable to have immediate access to it
new_project = env.create_project(name=PROJECT_NAME, description=PROJECT_DESCRIPTION)

# change description of a newly created project
new_project.alter(description=PROJECT_DESCRIPTION)

# delete a project

# first, the project need to be unloaded
new_project.unload()
# then delete the unloaded project,
# confirmation prompt will appear asking for a project name
new_project.delete()

# if a project is already unloaded, to delete it, it has to be retrieved
# via Environment object

# create an environment object
env = Environment(conn)
# list projects in the environment
projects = env.list_projects()
# get a project that you want to delete
project = projects['<index of a project to delete>']
# delete a project, confirmation prompt will appear asking for a project name
project.delete()


# Define variables which can be later used in a script
PROJECT_1_NAME = $project_1_name
PROJECT_2_NAME = $project_2_name

# compare settings of 2 projects (only differences will be stored into
# a DataFrame)
project1 = Project(connection=conn, name=PROJECT_1_NAME)
project2 = Project(connection=conn, name=PROJECT_2_NAME)
df_cmp = compare_project_settings(projects=[project, project1, project2], show_diff_only=True)

# Get the list of all settings and their values
project_settings = project.settings.list_properties()
# Get the list of all settings and their values with the settings description
project_settings_with_description = project.settings.list_properties(show_description=True)
# Get the list of all settings configuration (type, min/max value, options, etc.)
project_settings_types = project.settings.setting_types

# Define variables which can be later used in a script
CSV_FILE_EXPORT = $csv_file_export  # Name of file to which settings are exported
CSV_FILE_IMPORT = $csv_file_import  # Name of file from which settings are imported

# save/load settings of a project to/from a file (format can be 'csv',
# 'json' or 'pickle')
project.settings.to_csv(name=CSV_FILE_EXPORT)
# Export settings of a project to a csv file with the settings description
project.settings.to_csv(name=CSV_FILE_EXPORT, show_description=True)
project.settings.import_from(file=CSV_FILE_IMPORT)

# change a setting of a project
project.settings.cubeIndexGrowthUpperBound = 501

# Change setting with the use of Enum
project.settings.appendInfoForEmailDelivery = [
    FailedEmailDelivery.SUBSCRIPTION_NAME,
    FailedEmailDelivery.SUBSCRIPTION_RECIPIENT_NAME,
    FailedEmailDelivery.DELIVERY_STATUS,
    FailedEmailDelivery.DELIVERY_EMAIL_ADDRESS,
]
# Update multiple settings at once
project.settings.alter(maxEmailSubscriptionCount=100, maxExecutingJobsPerUser=50)
project.settings.update()

# print currently set value of Unified Quoting Behavior VldbSetting
print(project.vldb_settings['Quoting Behavior'].value)
# enable Unified Quoting Behavior
project.alter_vldb_settings(names_to_values={'Quoting Behavior': 1})
# disable Unified Quoting Behavior
project.alter_vldb_settings(names_to_values={'Quoting Behavior': 0})

# print currently available data engine versions
print(project.get_data_engine_versions())
# print data engine versions connected to environment projects
for project in env.list_projects():
    print(project.vldb_settings['AEVersion'].value)
# update data engine versions for all projects on environment
NEW_DATA_ENGINE_VERSION = $new_data_engine_version # Insert number related to new data engine version
for project in env.list_projects():
    project.update_data_engine_version(NEW_DATA_ENGINE_VERSION)

# Define variables which can be later used in a script
DATASOURCE_ID = $datasource_id  # Insert ID of datasource to add to project
# Get datasource instance with a given ID
datasource = DatasourceInstance(connection=conn, id=DATASOURCE_ID)
# Add datasource to project
project.add_datasource(datasources=[datasource])
# Remove datasource from project
project.remove_datasource(datasources=[datasource])
