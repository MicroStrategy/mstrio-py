from typing import TYPE_CHECKING

from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.sessions import FuturesSessionWithRenewal

if TYPE_CHECKING:
    from mstrio.connection import Connection


@unpack_information
@ErrorHandler("Error getting the table with ID: {id}")
def get_table(
    connection: 'Connection',
    id: str,
    project_id: str | None = None,
    changeset_id: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
):
    """Get a detailed definition for a specified table.

    Args:
        connection (object): MicroStrategy REST API connection object
        id (str): Table ID
        project_id (str, optional): Project ID
        changeset_id (str, optional): Changeset ID
        fields(list, optional): Comma separated top-level field whitelist.
            This allows client to selectively retrieve part of the
            response model.
        error_msg (str, optional): Custom Error Message for Error Handling
    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    if project_id is None:
        connection._validate_project_selected(),
        project_id = connection.project_id

    return connection.get(
        endpoint=f'/api/model/tables/{id}',
        headers={'X-MSTR-ProjectID': project_id, 'X-MSTR-Changeset': changeset_id},
        params={'fields': fields},
    )


@unpack_information
@ErrorHandler("Error listing tables")
def get_tables(
    connection: 'Connection',
    project_id: str | None = None,
    changeset_id: str | None = None,
    limit: int = None,
    offset: int = 0,
    fields: str | None = None,
    error_msg: str | None = None,
):
    """Get a list of all tables.

    Args:
        connection (object): MicroStrategy REST API connection object
        project_id (str, optional): Project ID
        changeset_id (str, optional): Changeset ID
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use None for no limit.
            Default is None.
        offset (int, optional): Starting point within the collection of
            returned results. Used to control paging behavior. Default is 0.
        fields(list, optional): Comma separated top-level field whitelist.
            This allows client to selectively retrieve part of the
            response model.
        error_msg (str, optional): Custom Error Message for Error Handling
    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    if project_id is None:
        connection._validate_project_selected(),
        project_id = connection.project_id

    return connection.get(
        endpoint='/api/model/tables',
        headers={'X-MSTR-ProjectID': project_id, 'X-MSTR-Changeset': changeset_id},
        params={'limit': limit, 'offset': offset, 'fields': fields},
    )


@unpack_information
@ErrorHandler("Error updating the table with ID: {id}")
def patch_table(
    connection: 'Connection',
    id: str,
    body: dict | None = None,
    column_merge_option: str | None = None,
    fields: dict | None = None,
    error_msg: str | None = None,
):
    """Update a detailed definition for a specified table in the changeset

    Args:
        connection (object): MicroStrategy REST API connection object
        id (str): Table ID
        body (dict): Table update body
        column_merge_option (str, optional): Defines a column merge option
            Available values: 'reuse_any', 'reuse_compatible_data_type',
            'reuse_matched_data_type'.
            If 'reuse_any', updates the column body type to use the most
                recent column definition.
            If 'reuse_compatible_data_type', updates the column body type
                to use the body type with the largest precision or scale.
            If 'reuse_matched_data_type', renames the column in newly added
                table to allow it to have different body types.
        fields(list, optional): Comma separated top-level field whitelist.
            This allows client to selectively retrieve part of the
            response model.
        error_msg (str, optional): Custom Error Message for Error Handling
    Returns:
        Complete HTTP response object. Expected status is 200.
    """
    with changeset_manager(connection) as changeset_id:
        return connection.patch(
            endpoint=f'/api/model/tables/{id}',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=body,
            params={'columnMergeOption': column_merge_option, 'fields': fields},
        )


@unpack_information
@ErrorHandler("Error creating the table")
def post_table(
    connection: 'Connection',
    data: dict,
    check_secondary_data_source_table: bool | None = None,
    column_merge_option: str | None = None,
    table_prefix_option: str | None = None,
    fields: str | None = None,
    error_msg: str | None = None,
):
    """Update a detailed definition for a specified table in the changeset

    Args:
        connection (object): MicroStrategy REST API connection object
        data (dict): Table creation data
        check_secondary_data_source_table (bool, optional):
            Available values: 'true', 'false'
            If 'true', finds compatible tables in the project.
                If a compatible table is found, the compatible table object
                information is returned. If no table is found,
                a new table is created.
            If 'false', a new table is created.
        column_merge_option (str, optional): Defines a column merge option
            Available values: 'reuse_any', 'reuse_compatible_data_type',
            'reuse_matched_data_type'.
            If 'reuse_any', updates the column data type to use the most
                recent column definition.
            If 'reuse_compatible_data_type', updates the column data type
                to use the data type with the largest precision or scale.
            If 'reuse_matched_data_type', renames the column in newly added
                table to allow it to have different data types.
        table_prefix_option (str, optional): Define the table prefix
            Available values: 'none', 'add_default_prefix', 'add_namespace'.
            If 'none', do not set table prefix.
            If 'add_default_prefix', applies the default prefix setting on
                warehouse catalog.
            If 'add_namespace', create a prefix same with namespace.
        fields(list, optional): Comma separated top-level field whitelist.
            This allows client to selectively retrieve part of the
            response model.
        error_msg (str, optional): Custom Error Message for Error Handling
    Returns:
        Complete HTTP response object. Expected status is 201.
    """
    with changeset_manager(connection) as changeset_id:
        return connection.post(
            endpoint='/api/model/tables',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            json=data,
            params={
                'checkSecondaryDataSourceTable': 'true'
                if check_secondary_data_source_table
                else 'false',
                'columnMergeOption': column_merge_option,
                'tablePrefixOption': table_prefix_option,
                'fields': fields,
            },
        )


@ErrorHandler("Error fetching available Warehouse Tables")
def get_available_warehouse_tables(
    connection: 'Connection',
    datasource_id: str,
    namespace_id: str,
    project_id: str | None = None,
    refresh: bool | None = None,
    error_msg: str | None = None,
):
    if project_id is None:
        connection._validate_project_selected(),
        project_id = connection.project_id

    return connection.get(
        endpoint=(
            f'/api/datasources/{datasource_id}/catalog/namespaces/{namespace_id}/tables'
        ),
        headers={'X-MSTR-ProjectID': project_id},
        params={'refresh': refresh},
    )


def get_table_async(
    future_session: FuturesSessionWithRenewal,
    id: str,
    changeset_id: str | None = None,
    project_id: str = None,
    fields=None,
):
    """Get definition of a single table by id, using FuturesSessionWithRenewal

    Args:
        future_session(object): `FuturesSessionWithRenewal` object to call
            MicroStrategy REST Server asynchronously
        id: ID of a table
        changeset_id: ID of a changeset
        project_id: Id of a project
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
    Return:
        Complete Future object.
    """
    return future_session.get(
        endpoint=f'/api/model/tables/{id}',
        headers={'X-MSTR-MS-Changeset': changeset_id, 'X-MSTR-ProjectID': project_id},
        params={'fields': fields},
    )


def get_available_warehouse_tables_async(
    future_session: FuturesSessionWithRenewal, datasource_id: str, namespace_id: str
):
    return future_session.get(
        endpoint=f'/api/datasources/{datasource_id}/catalog/namespaces/'
        f'{namespace_id}/tables',
        headers={'X-MSTR-ProjectID': future_session.connection.project_id},
    )


@ErrorHandler(err_msg="Error updating the structure of the table with ID: {id}")
def update_structure(
    connection: 'Connection',
    id: str,
    column_merge_option: str | None = None,
    fields: str | None = None,
    ignore_table_prefix: bool | None = None,
):
    """Update physical table structure.
    If table is missing, table cannot be updated. It will do nothing
    if the physical table is a free form sql table. If the table has
    secondary datasource, each physical table's schema in the secondary
    datasource list will also be checked. The update will be rejected
    if the new table structure does not meet secondary datasource condition
    (column missing, data type incompatible).

    Args:
        connection (object): MicroStrategy REST API connection object
        id (str): Logical table's ID. An identifier for the logical table
            object that the client wishes to invoke. The model service does
            not distinguish between logical and physical tables. A physical
            table is accessed as part of a logical table based on the physical
            table field.
        column_merge_option (str, optional): Defines a column merge option
            Available values: 'reuse_any', 'reuse_compatible_data_type',
            'reuse_matched_data_type'.
            If 'reuse_any', updates the column body type to use the most
                recent column definition.
            If 'reuse_compatible_data_type', updates the column body type
                to use the body type with the largest precision or scale.
            If 'reuse_matched_data_type', renames the column in newly added
                table to allow it to have different body types.
        fields (list, optional): Comma separated top-level field whitelist.
            This allows client to selectively retrieve part of the
            response model.
        ignore_table_prefix (bool, optional): If true, get all tables under
            current DB. There are three following situations:

                - If there is only one table that has same name as updated
                    table, update table structure using this table.
                - If there is no table that has same name as updated table,
                    throw error.
                - If there are multiple tables has same name as updated table,
                    throw error.

            If false, remain the current behavior.

            If not set, get the setting value from warehouse catalog. This
                behavior is same as column merge options.
    Returns:
        Complete HTTP response object.
    """
    with changeset_manager(connection) as changeset_id:
        return connection.post(
            endpoint=f'/api/model/tables/{id}/physicalTable/refresh',
            headers={'X-MSTR-MS-Changeset': changeset_id},
            params={
                'columnMergeOption': column_merge_option,
                'fields': fields,
                'ignoreTablePrefix': str(ignore_table_prefix).lower()
                if isinstance(ignore_table_prefix, bool)
                else ignore_table_prefix,
            },
        )
