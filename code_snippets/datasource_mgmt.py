"""This is the demo script to show how to manage datasources.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.datasources import (
    DatasourceConnection, DatasourceInstance, DatasourceLogin, DatasourceMap, DatasourceType,
    ExecutionMode, list_available_dbms, list_datasource_connections, list_datasource_instances,
    list_datasource_logins, list_datasource_mappings
)
from mstrio.connection import get_connection


PROJECT_NAME = '<Project_name>' # Insert project name here

# create a datasource login - all following information are concerning datasource logins management

LOGIN_NAME = '<Login_name>' # Insert name for login to datasouce here
NEW_LOGIN_NAME = '<Login_name>' # Insert new name for login to datasouce here
DATASOURCE_USER_NAME = '<DS_User_name>' # insert name of user in DataSource here
DATASOURCE_PASSWORD = '<DS_Password>' # Insert datasource password here
DATASOURCE_LOGIN_DESCRIPTION = '<DS_Login_Desc>' # Insert datasource login description
DATASOURCE_LOGIN_NEW_DESCRIPTIOM = '<DS_Login_Desc>' # Insert new datasource login description

# Following vaiables are for Datasource Connections management
DATASOURCE_CONNECTION_NAME = '<DS_Connection_Name>' # insert name of datasource connection here
DATASOURCE_CONNECTION_DESCRIPTION = '<DS_Connection_Desc>' # 'Insert description of datasource connection here'
DATASOURCE_CONNECTION_NEW_NAME = '<DS_Connection_Name>' # insert new name of datasource connection if you wish to change it
DATASOURCE_CONNECTION_NEW_DESCRIPTION ='<DS_Connection_Desc>' # insert new description of datasource connection if you wish to change it

# Following variables are for DataBase Management Systems (DMBSs)
DBMS_NAME = '<DBMS_Name>' # Insert name of DBMS that you want to find

# Following variables are for Datasource Instances management
DATASOURCE_INSTANCE_NAME = '<DS_Instance_Name>' # Insert name for created datasource instance here
DATASOURCE_INSTANCE_DESCRIPTION = '<DS_Instance_Desc>' # Insert description for created datasource instance here
DATASOURCE_INSTANCE_TABLE_PREFIX = '<DS_Instance_Prefix>' # Insert table prefix for created datasource instance here
DATASOURCE_INSTANCE_NEW_NAME = '<DS_Instance_Name>' # Insert name for edited datasource instance here
DATASOURCE_INSTANCE_NEW_DESCRIPTION = '<DS_Instance_Desc>' # Insert name for edited datasource instance here
DATASOURCE_INSTANCE_NEW_TABLE_PREFIX = '<DS_Instance_Prefix>' # Insert new table prefix for edited datasource instance here

# Following variables are for Datasource Mappings
DATASOURCE_MAP_ID = '<DS_Map_ID>' # Insert ID of datasource map that you wish to update
DATASOURCE_MAP_USERNAME = '<DS_Map_Username>' # Insert user name that you wish to be mapped with this datasource mapping

conn = get_connection(workstationData, project_name=PROJECT_NAME)

login = DatasourceLogin.create(connection=conn, name=LOGIN_NAME, username=DATASOURCE_USER_NAME,
                               password=DATASOURCE_PASSWORD, description=DATASOURCE_LOGIN_DESCRIPTION)

# update a datasource login
login.alter(name=NEW_LOGIN_NAME, description=DATASOURCE_LOGIN_NEW_DESCRIPTIOM)

# list properties of a datasource login
login.list_properties()

# delete a datasource login
login.delete(force=True)

# list all datasource logins
list_datasource_logins(connection=conn)

# create a datasource connection
ds_conn = DatasourceConnection.create(connection=conn, name=DATASOURCE_CONNECTION_NAME,
                                      description=DATASOURCE_CONNECTION_DESCRIPTION,
                                        # the ExecutionMode values can be found in  datasources/datasource_connection.py
                                      execution_mode=ExecutionMode.SYNCHRONOUS,
                                      datasource_login=login)

# update a datasource connection
ds_conn.alter(name=DATASOURCE_CONNECTION_NEW_NAME, description=DATASOURCE_CONNECTION_NEW_DESCRIPTION)

# list properties of a datasource connection
ds_conn.list_properties()

# delete a datasource connection
ds_conn.delete(force=True)

# list all datasource connections
list_datasource_connections(connection=conn)

# get a dbms by name
dbms = list_available_dbms(connection=conn, name=DBMS_NAME)

# create a datasource instance
ds_instance = DatasourceInstance.create(connection=conn, name=DATASOURCE_INSTANCE_NAME,
                                        description=DATASOURCE_INSTANCE_DESCRIPTION, dbms=dbms,
                                        datasource_connection=ds_conn,
                                        table_prefix=DATASOURCE_INSTANCE_TABLE_PREFIX,
                                        # the DatasourceType values can be found in  datasources/datasource_instance.py
                                        datasource_type=DatasourceType.RESERVED)

# update a datasource instance
ds_instance.alter(name=DATASOURCE_INSTANCE_NEW_NAME, description=DATASOURCE_INSTANCE_NEW_DESCRIPTION,
                  table_prefix=DATASOURCE_INSTANCE_NEW_TABLE_PREFIX)

# list properties of a datasource instance
ds_instance.list_properties()

# delete a datasource instance
ds_instance.delete(force=True)

# list all datasources by environment
list_datasource_instances(connection=conn)

# list all datasources by project
list_datasource_instances(connection=conn, project=PROJECT_NAME)

# list all datasources by datasource connection
list_datasource_instances(connection=conn, datasource_connection={"id": ds_conn.id})

# create a datasource map
ds_map = DatasourceMap.create(connection=conn, project=PROJECT_NAME, user=DATASOURCE_MAP_USERNAME, ds_connection=ds_conn,
                              datasource=ds_instance, login=login)

# initialise a datasource map
ds_map = DatasourceMap(connection=conn, id=DATASOURCE_MAP_ID)

# list all datasource maps
list_datasource_mappings(connection=conn)

# delete a datasource map
ds_map.delete(force=True)
