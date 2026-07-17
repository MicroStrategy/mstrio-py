"""
Flow Step Template: Execute SQL Query
Script Result Type: text

This workflow template works OOTB after providing values for all required
Variables.

It represents executing SQL query end returning its outcome action.

The Script will return result of a query, as stringified object.

Either `$datasource_instance_id` or `$datasource_instance_name` is required.

The workflow currently assumes:
- That the connection will be established via `get_connection`
- That the Datasource Instance which will trigger the SQL is already created,
    configured and available - and will be identified by name
"""

from mstrio.connection import get_connection, Connection
from mstrio.datasources.datasource_instance import DatasourceInstance

PROJECT_NAME = $project_name

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
conn = get_connection(connectionData, project=PROJECT_NAME)

DS_ID = $datasource_instance_id or None
DS_NAME = $datasource_instance_name or None
SQL_QUERY = $sql_query

dsi = DatasourceInstance(conn, id=DS_ID, name=DS_NAME)

result = dsi.execute_query(
    project_id=conn.project_id,
    query=SQL_QUERY,
)


def get_results():
    return result
