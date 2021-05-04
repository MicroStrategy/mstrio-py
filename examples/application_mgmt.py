"""This is the demo script to show how administrator can manage applications
and its settings.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.server.application import Application, compare_application_settings
from mstrio.server.environment import Environment

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, application_name="MicroStrategy Tutorial",
                  login_mode=1)
env = Environment(connection=conn)

# get list of all applications or those just loaded
all_applications = env.list_applications()
loaded_applications = env.list_loaded_applications()

# get application with a given name
app = Application(connection=conn, name="MicroStrategy Tutorial")
# idle/resume an application on a given node(s) (name(s) of existing node(s)
# should be used)
app.idle(on_nodes=["node1"])
app.resume(on_nodes="node1")
# unload/load an application from/to a given node(s) (name(s) of existing
# node(s) should be used)
app.unload(on_nodes="node1")
app.load(on_nodes="node1")

# get settings of an application as a dataframe
app_settings_df = app.settings.to_dataframe

# create an application and store it in variable to have immediate access to it
new_app = env.create_application(name="Demo Application 1", description="some description")
# change description of a newly created application
new_app.alter(
    description="This application is used to present creation of an application as a demo")

# compare settings of 2 applications (only differences will be stored into
# a DataFrame)
app1 = Application(connection=conn, name="Consolidated Education Project")
app2 = Application(connection=conn, name="Platform Analytics")
df_cmp = compare_application_settings(applications=[app, app1, app2], show_diff_only=True)

# save/load settings of an application to/from a file (format can be 'csv',
# 'json' or 'pickle')
app.settings.to_csv(name="mstr_tutorial_settings.csv")
app.settings.import_from(file="mstr_tutorial_settings.csv")

# change a setting of an application
app.settings.cubeIndexGrowthUpperBound = 501
app.settings.update()
