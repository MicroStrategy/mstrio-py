"""This is the demo script to show how administrator can manage projects
and its settings.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.server import Project, compare_project_settings, Environment

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)
env = Environment(connection=conn)

# get list of all projects or those just loaded
all_projects = env.list_projects()
loaded_projects = env.list_loaded_projects()

# get project with a given name
project = Project(connection=conn, name="MicroStrategy Tutorial")
# idle/resume an project on a given node(s) (name(s) of existing node(s)
# should be used)
project.idle(on_nodes=["node1"])
project.resume(on_nodes="node1")
# unload/load an project from/to a given node(s) (name(s) of existing
# node(s) should be used)
project.unload(on_nodes="node1")
project.load(on_nodes="node1")

# get settings of an project as a dataframe
project_settings_df = project.settings.to_dataframe

# create an project and store it in variable to have immediate access to it
new_project = env.create_project(name="Demo Project 1", description="some description")
# change description of a newly created project
new_project.alter(
    description="This project is used to present creation of a project as a demo")

# compare settings of 2 projects (only differences will be stored into
# a DataFrame)
project1 = Project(connection=conn, name="Consolidated Education Project")
project2 = Project(connection=conn, name="Platform Analytics")
df_cmp = compare_project_settings(projects=[project, project1, project2], show_diff_only=True)

# save/load settings of an project to/from a file (format can be 'csv',
# 'json' or 'pickle')
project.settings.to_csv(name="mstr_tutorial_settings.csv")
project.settings.import_from(file="mstr_tutorial_settings.csv")

# change a setting of an project
project.settings.cubeIndexGrowthUpperBound = 501
project.settings.update()
