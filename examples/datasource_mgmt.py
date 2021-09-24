"""This is the demo script to show how to manage datasources.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.connection import Connection
from mstrio.server import Project
from mstrio.users_and_groups import User
from mstrio.datasources import (DatasourceType, ExecutionMode, DatasourceConnection,
                                DatasourceInstance, DatasourceLogin, DatasourceMap,
                                list_datasource_connections, list_available_dbms,
                                list_datasource_instances, list_datasource_logins,
                                list_datasource_mappings)

base_url = "https://<>/MicroStrategyLibrary/api"
username = "some_username"
password = "some_password"
conn = Connection(base_url, username, password, project_name="MicroStrategy Tutorial",
                  login_mode=1)

# create a datasource login
login = DatasourceLogin.create(connection=conn, name='login_name', username='username',
                               password=password, description='Description of a login')

# update a datasource login
login.alter(name='changed', description='Changed description of a login')

# list properties of a datasource login
login.list_properties()

# delete a datasource login
login.delete(force=True)

# list all datasource logins
list_datasource_logins(connection=conn)

# create a datasource connection
ds_conn = DatasourceConnection.create(connection=conn, name='conn_name',
                                      description='Description a connection',
                                      execution_mode=ExecutionMode.ASYNCH_CONNECTION,
                                      datasource_login=login)

# update a datasource connection
ds_conn.alter(name='changed', description='Changed description of a connection')

# list properties of a datasource connection
ds_conn.list_properties()

# delete a datasource connection
ds_conn.delete(force=True)

# list all datasource connections
list_datasource_connections(connection=conn)

# get a dbms by name
dbms = list_available_dbms(connection=conn, name='PostgreSQL')

# create a datasource instance
ds_instance = DatasourceInstance.create(connection=conn, name='instance_name',
                                        description='Description of a datasource', dbms=dbms,
                                        datasource_connection=ds_conn,
                                        datasource_type=DatasourceType.RESERVED)

# update a datasource instance
ds_instance.alter(name='changed', description='Changed description of a datasource instance',
                  table_prefix='new_table_prefix')

# list properties of a datasource instance
ds_instance.list_properties()

# delete a datasource instance
ds_instance.delete(force=True)

# list all datasources by environment
list_datasource_instances(connection=conn)

# get project by name
project = Project(connection=conn, name="MicroStrategy Tutorial")

# list all datasources by project
list_datasource_instances(connection=conn, project=project)

# list all datasources by datasource connection
list_datasource_instances(connection=conn, datasource_connection={"id": ds_conn.id})

# get a user
user = User(connection=conn, username='mstr')
# create a datasource map
ds_map = DatasourceMap.create(connection=conn, project=project, user=user, ds_connection=ds_conn,
                              datasource=ds_instance, login=login)

# initialise a datasource map
example_ds_map_id = '1234567890A1234567890A1234567890'
ds_map = DatasourceMap(connection=conn, id=example_ds_map_id)

# list all datasource maps
list_datasource_mappings(connection=conn)

# delete a datasource map
ds_map.delete(force=True)
