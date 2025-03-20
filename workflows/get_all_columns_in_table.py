"""List all the columns for all available tables

1. Connect to the environment using data from workstation
2a. This path is executed when the table is specified in argument of function
3a. Get whole representation of table based on its id
4a. Unpack the response and for the given table get all columns in a specified
    format with  subtype, object id and name
2b. This path is executed when the table is not specified in argument of function
3b. Get all tables in the project specified in the connection object
4b. Get whole representation of each table based on their ids
5b. Unpack the response and for each table return all columns in a specified
    format with subtype, object id and name
"""
from typing import Optional, Union

from mstrio.api import tables
from mstrio.connection import Connection, get_connection
from mstrio.modeling.schema.helpers import SchemaObjectReference
from mstrio.utils.api_helpers import async_get
from mstrio.utils.wip import module_wip, WipLevels

module_wip(globals(), level=WipLevels.PREVIEW)


def list_table_columns(
    connection: Connection, table: Optional[Union[SchemaObjectReference, str]] = None
) -> dict:
    """List all the columns for a given table, if tables is not specified,
    list all the columns for all available tables.

    Args:
        connection: Strategy One connection object returned
            by `connection.Connection()`
        table: SchemaObjectReference of a table or table id

    Returns:
        dictionary of all the columns for a given table, or for all tables
        if table is not specified e.g.
        {'TABLE_NAME':[
            SchemaObjectReference(sub_type='column', object_id='1111',
                                  name='column_name'),
            SchemaObjectReference(sub_type='column', object_id='2222',
                                  name='other_column_name')
        ]}

    """

    def unpack(table_res):
        columns_list_dict = table_res['physicalTable']['columns']
        return [
            SchemaObjectReference(
                col['information']['subType'],
                col['information']['objectId'],
                col['information']['name'],
            )
            for col in columns_list_dict
        ]

    if table:
        table_id = table if isinstance(table, str) else table.object_id
        table_res = tables.get_table(
            connection, table_id, project_id=connection.project_id
        ).json()
        return {table_res['information']['name']: unpack(table_res)}
    else:
        table_res = tables.get_tables(
            connection, project_id=connection.project_id
        ).json()
        ids = [tab['information']['objectId'] for tab in table_res['tables']]
        tables_async = async_get(tables.get_table_async, connection, ids)
        return {table['information']['name']: unpack(table) for table in tables_async}


# connect to environment without providing user credentials
# variable `workstationData` is stored within Workstation
conn = get_connection(workstationData, 'MicroStrategy Tutorial')

# list all the columns for all available tables
list_table_columns(conn)
