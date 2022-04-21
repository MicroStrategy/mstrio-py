"""This is the demo script to show how administrator can manage projects
and its settings.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.server import compare_project_settings, Environment, Project
from mstrio.connection import get_connection

PROJECT_NAME = '<Project_name>'  # Insert name of project to interact with
NODE_NAME = '<Node_name>'  # Insert name of node, that has a project, to load or unload it

PROJECT_DESCRIPTION = '<Description_of_project>'  # Insert description of newly created project

# These strings are used for project settings comparison
PROJECT_1_NAME = '<Project_name>'
PROJECT_2_NAME = '<Project_name>'
CSV_FILE_EXPORT_IMPORT = 'path/to/file.csv'  # Name of file to/from which settings are imported

conn = get_connection(workstationData, project_name=PROJECT_NAME)
env = Environment(connection=conn)

# get list of all projects or those just loaded
all_projects = env.list_projects()
loaded_projects = env.list_loaded_projects()

# get project with a given name
project = Project(connection=conn, name=PROJECT_NAME)
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

# create a project and store it in variable to have immediate access to it
new_project = env.create_project(name=PROJECT_NAME, description=PROJECT_DESCRIPTION)

# change description of a newly created project
new_project.alter(description=PROJECT_DESCRIPTION)

# compare settings of 2 projects (only differences will be stored into
# a DataFrame)
project1 = Project(connection=conn, name=PROJECT_1_NAME)
project2 = Project(connection=conn, name=PROJECT_2_NAME)
df_cmp = compare_project_settings(projects=[project, project1, project2], show_diff_only=True)

# save/load settings of a project to/from a file (format can be 'csv',
# 'json' or 'pickle')
project.settings.to_csv(name=CSV_FILE_EXPORT_IMPORT)
project.settings.import_from(file=CSV_FILE_EXPORT_IMPORT)

# change a setting of a project
project.settings.cubeIndexGrowthUpperBound = 501
project.settings.update()
