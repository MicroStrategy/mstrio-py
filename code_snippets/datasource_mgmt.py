"""This is the demo script to show how to manage datasources.

This script will not work without replacing parameters with real values.
Its basic goal is to present what can be done with this module and to
ease its usage.
"""

from mstrio.datasources import (
    DatasourceConnection,
    DatasourceInstance,
    DatasourceLogin,
    DatasourceMap,
    DatasourceType,
    ExecutionMode,
    Locale,
    list_available_dbms,
    list_datasource_connections,
    list_datasource_instances,
    list_datasource_logins,
    list_datasource_mappings,
    list_locales,
    Dbms
)
from mstrio.connection import get_connection


# Define variables which can be later used in a script
PROJECT_ID = $project_id  # Project ID to connect to
PROJECT_NAME = $project_name  # Insert project name to connect to

conn = get_connection(workstationData, project_name=PROJECT_NAME)

# Manage datasource logins
# Get a list of datasource logins
datasource_login_list = list_datasource_logins(connection=conn)
print(datasource_login_list)

# Define variables which can be later used in a script
DATASOURCE_LOGIN_ID = $datasource_login_id  # Insert ID for login to datasource here
DATASOURCE_LOGIN_NAME = $datasource_login_name  # Insert name for login to datasource here

# Get datasource login by id
datasource_login = DatasourceLogin(conn, id=DATASOURCE_LOGIN_ID)
print(datasource_login)

# Get datasource login by name
datasource_login = DatasourceLogin(conn, name=DATASOURCE_LOGIN_NAME)
print(datasource_login)

# Define variables which can be later used in a script
NEW_DATASOURCE_LOGIN_NAME = $new_datasource_login_name  # Insert name for new login to datasource here
NEW_DATASOURCE_USERNAME = $new_datasource_username  # Insert name of user in Datasource here
NEW_DATASOURCE_PASSWORD = $new_datasource_password  # Insert datasource password here
NEW_DATASOURCE_LOGIN_DESCRIPTION = $new_datasource_login_description  # Insert new datasource login description

# Create new datasource login
datasource_login = DatasourceLogin.create(
    connection=conn,
    name=NEW_DATASOURCE_LOGIN_NAME,
    username=NEW_DATASOURCE_USERNAME,
    password=NEW_DATASOURCE_PASSWORD,
    description=NEW_DATASOURCE_LOGIN_DESCRIPTION,
)
print(datasource_login)

# Define variables which can be later used in a script
DATASOURCE_LOGIN_NEW_NAME = $datasource_login_new_name  # Insert new name for login to datasource here
DATASOURCE_LOGIN_NEW_DESCRIPTION = $datasource_login_new_description  # Insert new datasource login description

# Update a datasource login
datasource_login.alter(
    name=DATASOURCE_LOGIN_NEW_NAME,
    description=DATASOURCE_LOGIN_NEW_DESCRIPTION,
)
print(datasource_login)

# List properties of a datasource login
print(datasource_login.list_properties())

# Delete a datasource login
datasource_login.delete(force=True)

# Manage datasource connections
# List all datasource connections
datasource_conn_list = list_datasource_connections(connection=conn)
print(datasource_conn_list)

# Define variables which can be later used in a script
DATASOURCE_CONNECTION_ID = $datasource_connection_id  # Insert ID of datasource connection here
DATASOURCE_CONNECTION_NAME = $datasource_connection_name  # Insert name of datasource connection here

# Get datasource connection by id
datasource_connection = DatasourceConnection(conn, id=DATASOURCE_CONNECTION_ID)
print(datasource_connection)

# Get datasource connection by name
datasource_connection = DatasourceConnection(conn, name=DATASOURCE_CONNECTION_NAME)
print(datasource_connection)

# Define variables which can be later used in a script
NEW_DATASOURCE_CONNECTION_NAME = $new_datasource_connection_name  # Insert new name of datasource connection here
NEW_DATASOURCE_CONNECTION_DESCRIPTION = $new_datasource_connection_description  # Insert new description of datasource connection here

# Create a new datasource connection
datasource_connection = DatasourceConnection.create(
    connection=conn,
    name=NEW_DATASOURCE_CONNECTION_NAME,
    description=NEW_DATASOURCE_CONNECTION_DESCRIPTION,
    # the ExecutionMode values can be found in datasources/datasource_connection.py
    execution_mode=ExecutionMode.SYNCHRONOUS,
    datasource_login=DATASOURCE_LOGIN_ID,
)

# Define variables which can be later used in a script
DATASOURCE_CONNECTION_NEW_NAME = $datasource_connection_new_name  # Insert new name of datasource connection
DATASOURCE_CONNECTION_NEW_DESCRIPTION = $datasource_connection_new_description  # Insert new description of datasource connection

# Update a datasource connection
datasource_connection.alter(
    name=DATASOURCE_CONNECTION_NEW_NAME,
    description=DATASOURCE_CONNECTION_NEW_DESCRIPTION,
)
print(datasource_connection)

# List properties of a datasource connection
print(datasource_connection.list_properties())

# Delete a datasource connection
datasource_connection.delete(force=True)


# Note that conversion to DSN-less is supported on certified gateways:
# Amazon Redshift; Azure Synapse Analytics; ExasolI;
# BM Db2 for Linux, UNIX and Windows; MySQL; Oracle; PostgreSQL;
# Salesforce; Cloudera Hive; Cloudera Impala; Google BigQuery; Spark SQL;
# SAP HANA; Snowflake; SQL Server; Teradata

# Define variables which can be later used in a script
DATASOURCE_CONNECTION_ID_DSN = $datasource_connection_id_dsn  # Insert id of datasource connection that had DSN connection string

# Initialize datasource connection object
ds_conn = DatasourceConnection(conn, id=DATASOURCE_CONNECTION_ID_DSN)

# List datasource connection properites before conversion
print(ds_conn.list_properties())

# This method is supported from Update 9 server version
# Convert datasource connection to DSN-less
ds_conn.convert_to_dsn_less()

# List datasource connection properites after conversion
print(ds_conn.list_properties())

# Define variables which can be later used in a script
DATASOURCE_CONNECTION_ID_DSN_LIST = $datasource_connection_id_dsn_list  # Insert IDs for datasource connections here

# Convert datasource connections one by one from list
for ds_conn_id in DATASOURCE_CONNECTION_ID_DSN_LIST:
    ds_conn = DatasourceConnection(conn, id=ds_conn_id)
    # This method is supported from Update 9 server version
    ds_conn.convert_to_dsn_less()


# Manage datasource instances
# List all datasources
datasources = list_datasource_instances(connection=conn)
print(datasources)

# List all datasources by project
datasources = list_datasource_instances(connection=conn, project=PROJECT_ID)
print(datasources)

# List all datasources by datasource connection
datasources = list_datasource_instances(
    connection=conn, datasource_connection={'id': DATASOURCE_CONNECTION_ID}
)
print(datasources)

# Define variables which can be later used in a script
DATASOURCE_INSTANCE_ID = $datasource_instance_id  # Insert ID for datasource instance here
DATASOURCE_INSTANCE_NAME = $datasource_instance_name  # Insert name for datasource instance here

# Get datasource instance by id
datasource_instance = DatasourceInstance(conn, id=DATASOURCE_INSTANCE_ID)
print(datasource_instance)

# Get datasource instance by name
datasource_instance = DatasourceInstance(conn, name=DATASOURCE_INSTANCE_NAME)
print(datasource_instance)

# List dbms
dbms = list_available_dbms(connection=conn)
print(dbms)

# Define variables which can be later used in a script
DBMS_ID = $dbms_id  # Insert ID of DBMS that you want to find
DBMS_NAME = $dbms_name  # Insert name of DBMS that you want to find

# Get a DBMS by id
dbms = Dbms(conn, id=DBMS_ID)
print(dbms)

# Get a DBMS by name
dbms = Dbms(conn, name=DBMS_NAME)
print(dbms)

# Define variables which can be later used in a script
NEW_DATASOURCE_INSTANCE_NAME = $new_datasource_instance_name  # Insert name for datasource instance here
NEW_DATASOURCE_INSTANCE_DESCRIPTION = $new_datasource_instance_description  # Insert description for datasource instance here
NEW_DATASOURCE_INSTANCE_TABLE_PREFIX = $new_datasource_instance_table_prefix  # Insert table prefix for datasource instance here

# Create a datasource instance
datasource_instance = DatasourceInstance.create(
    connection=conn,
    name=NEW_DATASOURCE_INSTANCE_NAME,
    description=NEW_DATASOURCE_INSTANCE_DESCRIPTION,
    dbms=DBMS_ID,
    datasource_connection=DATASOURCE_CONNECTION_ID,
    table_prefix=NEW_DATASOURCE_INSTANCE_TABLE_PREFIX,
    # The DatasourceType values can be found in datasources/datasource_instance.py
    datasource_type=DatasourceType.RESERVED
)
print(datasource_instance)

# Define variables which can be later used in a script
DATASOURCE_INSTANCE_NEW_NAME = $datasource_instance_new_name  # Insert new name for edited datasource instance here
DATASOURCE_INSTANCE_NEW_DESCRIPTION = $datasource_instance_new_description  # Insert new description for edited datasource instance here
DATASOURCE_INSTANCE_TABLE_NEW_PREFIX = $datasource_instance_table_new_prefix  # Insert new table prefix for edited datasource instance here

# Update a datasource instance
datasource_instance.alter(
    name=DATASOURCE_INSTANCE_NEW_NAME,
    description=DATASOURCE_INSTANCE_NEW_DESCRIPTION,
    table_prefix=DATASOURCE_INSTANCE_TABLE_NEW_PREFIX
)
print(datasource_instance)

# List properties of a datasource instance
print(datasource_instance.list_properties())

# Delete a datasource instance
datasource_instance.delete(force=True)


# Note that conversion to DSN-less is supported on certified gateways:
# Amazon Redshift; Azure Synapse Analytics; ExasolI;
# BM Db2 for Linux, UNIX and Windows; MySQL; Oracle; PostgreSQL;
# Salesforce; Cloudera Hive; Cloudera Impala; Google BigQuery; Spark SQL;
# SAP HANA; Snowflake; SQL Server; Teradata

# Define variables which can be later used in a script
DATASOURCE_INSTANCE_ID_DSN = $datasource_instance_id_dsn  # Insert ID for datasource instance here

# Get datasource instance by id
ds_instance = DatasourceInstance(conn, id=DATASOURCE_INSTANCE_ID_DSN)

# This method is supported from Update 9 server version
# Convert datasource embedded connection from DSN to DSN-less format
ds_instance.convert_ds_connection_to_dsn_less()

# Define variables which can be later used in a script
DATASOURCE_INSTANCE_ID_DSN_LIST = $datasource_instance_id_dsn_list  # Insert IDs for datasource instances here

# Convert datasource instance embedded connection one by one from list
for ds_id in DATASOURCE_INSTANCE_ID_DSN_LIST:
    ds_instance = DatasourceInstance(conn, id=ds_id)
    # This method is supported from Update 9 server version
    ds_instance.convert_ds_connection_to_dsn_less()


# Manage connection mappings

# List all locales
locales_list = list_locales(connection=conn)
print(locales_list)

# Define variables which can be later used in a script
LOCALE_ID = $locale_id
LOCALE_NAME = $locale_name
LOCALE_ABBREVIATION = $locale_abbreviation

# Initialize locale object by id
locale = Locale(conn, id=LOCALE_ID)
print(locale)

# Initialize locale object by name
locale = Locale(conn, name=LOCALE_NAME)
print(locale)

# Initialize locale object by abbreviation
locale = Locale(conn, abbreviation=LOCALE_ABBREVIATION)
print(locale)

# List all connection mappings
connection_mapping_list = list_datasource_mappings(connection=conn)
print(connection_mapping_list)

# Define a variable which can be later used in a script
USER_OR_USER_GROUP_ID = $user_or_user_group_id  # Insert ID of a user or user group
                                                # that you wish to be mapped
                                                # with a connection mapping

# List connection mappings filtered by user
connection_mapping_list = list_datasource_mappings(
    connection=conn,
    user=USER_OR_USER_GROUP_ID,
)
print(connection_mapping_list)

# List connection mappings filtered by datasource connection
connection_mapping_list = list_datasource_mappings(
    connection=conn,
    ds_connection=DATASOURCE_CONNECTION_ID,
)
print(connection_mapping_list)

# List connection mappings filtered by datasource instance
connection_mapping_list = list_datasource_mappings(
    connection=conn,
    datasource=DATASOURCE_INSTANCE_ID,
)
print(connection_mapping_list)

# List connection mappings filtered by datasource login
connection_mapping_list = list_datasource_mappings(
    connection=conn,
    login=DATASOURCE_LOGIN_ID,
)
print(connection_mapping_list)

# List connection mappings filtered by locale ID
connection_mapping_list = list_datasource_mappings(
    connection=conn,
    locale=LOCALE_ID,
)
print(connection_mapping_list)

# List connection mappings filtered by locale name
connection_mapping_list = list_datasource_mappings(
    connection=conn,
    locale=LOCALE_NAME,
)
print(connection_mapping_list)

# List connection mappings filtered by locale abbreviation
connection_mapping_list = list_datasource_mappings(
    connection=conn,
    locale=LOCALE_ABBREVIATION,
)
print(connection_mapping_list)

# List default connection mappings for a project
connection_mapping_list = list_datasource_mappings(
    connection=conn,
    default_connection_map=True,
    project=PROJECT_ID,
)
print(connection_mapping_list)

# Define a variable which can be later used in a script
CONNECTION_MAPPING_ID = $connection_mapping_id  # Insert ID of connection mapping

# Initialise a connection mapping
connection_mapping = DatasourceMap(connection=conn, id=CONNECTION_MAPPING_ID)
print(connection_mapping)

# Initialise a default connection mapping by id for a project
connection_mapping = DatasourceMap(
    connection=conn,
    id=CONNECTION_MAPPING_ID,
    default_connection_map=True,
    project=PROJECT_ID,
)
print(connection_mapping)

# Initialise a default connection mapping for a project if only one default connection mapping
# exists for a project
connection_mapping = DatasourceMap(
    connection=conn,
    default_connection_map=True,
    project=PROJECT_ID,
)
print(connection_mapping)

# Create a connection mapping with default locale
connection_mapping = DatasourceMap.create(
    connection=conn,
    project=PROJECT_ID,
    user=USER_OR_USER_GROUP_ID,
    ds_connection=DATASOURCE_CONNECTION_ID,
    datasource=DATASOURCE_INSTANCE_ID,
    login=DATASOURCE_LOGIN_ID,
)
print(connection_mapping)

# Create a connection mapping with locale's id
connection_mapping = DatasourceMap.create(
    connection=conn,
    project=PROJECT_ID,
    user=USER_OR_USER_GROUP_ID,
    ds_connection=DATASOURCE_CONNECTION_ID,
    datasource=DATASOURCE_INSTANCE_ID,
    login=DATASOURCE_LOGIN_ID,
    locale=LOCALE_ID
)
print(connection_mapping)
# Create a connection mapping with locale's name
connection_mapping = DatasourceMap.create(
    connection=conn,
    project=PROJECT_ID,
    user=USER_OR_USER_GROUP_ID,
    ds_connection=DATASOURCE_CONNECTION_ID,
    datasource=DATASOURCE_INSTANCE_ID,
    login=DATASOURCE_LOGIN_ID,
    locale=LOCALE_NAME
)
print(connection_mapping)

# Create a connection mapping with locale's abbreviation
connection_mapping = DatasourceMap.create(
    connection=conn,
    project=PROJECT_ID,
    user=USER_OR_USER_GROUP_ID,
    ds_connection=DATASOURCE_CONNECTION_ID,
    datasource=DATASOURCE_INSTANCE_ID,
    login=DATASOURCE_LOGIN_ID,
    locale=LOCALE_ABBREVIATION
)
print(connection_mapping)

# Define variables which can be later used in a script
CONNECTION_MAPPING_NEW_USER_OR_USER_GROUP = $connection_mapping_new_user_or_user_group  # Insert new user or usergroup ID for connection mapping
CONNECTION_MAPPING_NEW_LOGIN = $connection_mapping_new_login  # Insert new login ID for connection mapping

# Alter connection mapping
# NOTE: Altering connection mapping will change its ID
connection_mapping.alter(
    user=CONNECTION_MAPPING_NEW_USER_OR_USER_GROUP,
    login=CONNECTION_MAPPING_NEW_LOGIN,
)
print(connection_mapping)

# Alter connection mapping's locale by id
connection_mapping.alter(locale=LOCALE_ID)
print(connection_mapping)

# Alter connection mapping's locale by name
connection_mapping.alter(locale=LOCALE_NAME)
print(connection_mapping)

# Alter connection mapping's locale by abbreviation
connection_mapping.alter(locale=LOCALE_ABBREVIATION)
print(connection_mapping)

# Delete a connection mapping
connection_mapping.delete(force=True)
