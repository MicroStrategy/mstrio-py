"""
Flow Step Template: Convert Datasource Connection to DSN-less
Script Result Type: text

This workflow template works OOTB after providing values for all required
Variables.

It represents converting Datasource Connection to DSN-less action.

The Script will return connection string.

Either `$datasource_connection_id` or `$datasource_connection_name` is required.

The workflow currently assumes:
- That the connection will be established via `get_connection`
- That the Datasource Connection which will be converted is already created,
    configured and available - and will be identified by name
"""

from mstrio.connection import get_connection, Connection
from mstrio.datasources.datasource_connection import DatasourceConnection

# if the connection requires explicitly provided `Connection` details,
# `Connection` object with provided parameters can be used here instead
conn = get_connection(connectionData)

DC_ID = $datasource_connection_id or None
DC_NAME = $datasource_connection_name or None

dsc = DatasourceConnection(conn, id=DC_ID, name=DC_NAME)

dsc.convert_to_dsn_less()


def get_results():
    return dsc.connection_string
