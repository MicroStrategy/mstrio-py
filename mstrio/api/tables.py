from typing import Optional, TYPE_CHECKING

from mstrio.utils.api_helpers import changeset_manager, unpack_information
from mstrio.utils.error_handlers import ErrorHandler
from mstrio.utils.sessions import FuturesSessionWithRenewal

if TYPE_CHECKING:
    from mstrio.connection import Connection


@unpack_information
@ErrorHandler("Error getting the table with ID: {id}")
def get_table(
    connection: "Connection",
    id: str,
    project_id: Optional[str] = None,
    changeset_id: Optional[str] = None,
    fields: Optional[str] = None,
    error_msg: Optional[str] = None,
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
        url=f"{connection.base_url}/api/model/tables/{id}",
        headers={
            "X-MSTR-ProjectID": project_id, "X-MSTR-Changeset": changeset_id
        },
        params={"fields": fields},
    )


@unpack_information
@ErrorHandler("Error listing tables")
def get_tables(
    connection: "Connection",
    project_id: Optional[str] = None,
    changeset_id: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    fields: Optional[str] = None,
    error_msg: Optional[str] = None,
):
    """Get a list of all tables.

    Args:
        connection (object): MicroStrategy REST API connection object
        project_id (str, optional): Project ID
        changeset_id (str, optional): Changeset ID
        limit (int, optional): Maximum number of items returned for a single
            request. Used to control paging behavior. Use -1 for no limit.
            Default is 1000.
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
        url=f"{connection.base_url}/api/model/tables",
        headers={
            "X-MSTR-ProjectID": project_id, "X-MSTR-Changeset": changeset_id
        },
        params={
            "limit": limit, "offset": offset, "fields": fields
        },
    )


@unpack_information
@ErrorHandler("Error updating the table with ID: {id}")
def patch_table(
    connection: "Connection",
    id: str,
    body: dict,
    column_merge_option: Optional[str] = None,
    fields: Optional[dict] = None,
    error_msg: Optional[str] = None,
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
            url=f"{connection.base_url}/api/model/tables/{id}",
            headers={"X-MSTR-MS-Changeset": changeset_id},
            json=body,
            params={
                "columnMergeOption": column_merge_option, "fields": fields
            },
        )


@unpack_information
@ErrorHandler("Error creating the table")
def post_table(
    connection: "Connection",
    data: dict,
    check_secondary_data_source_table: Optional[bool] = None,
    column_merge_option: Optional[str] = None,
    table_prefix_option: Optional[str] = None,
    fields: Optional[str] = None,
    error_msg: Optional[str] = None,
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
            url=f"{connection.base_url}/api/model/tables",
            headers={"X-MSTR-MS-Changeset": changeset_id},
            json=data,
            params={
                "checkSecondaryDataSourceTable": "true"
                if check_secondary_data_source_table else "false",
                "columnMergeOption": column_merge_option,
                "tablePrefixOption": table_prefix_option,
                "fields": fields,
            },
        )


@ErrorHandler("Error fetching available Warehouse Tables")
def get_available_warehouse_tables(
    connection: "Connection",
    datasource_id: str,
    namespace_id: str,
    project_id: Optional[str] = None,
    error_msg: Optional[str] = None,
):
    if project_id is None:
        connection._validate_project_selected(),
        project_id = connection.project_id

    url = (
        f"{connection.base_url}/api/datasources/{datasource_id}/catalog/"
        f"namespaces/{namespace_id}/tables"
    )
    return connection.get(
        url,
        headers={
            "X-MSTR-ProjectID": project_id,
        },
    )


def get_table_async(
    session: FuturesSessionWithRenewal,
    connection: "Connection",
    id: str,
    changeset_id: Optional[str] = None,
    project_id: str = None,
    fields=None,
):
    """Get definition of a single table by id, using FuturesSessionWithRenewal

    Args:
        connection: MicroStrategy REST API connection object
        id: ID of a table
        changeset_id: ID of a changeset
        project_id: Id of a project
        fields: A whitelist of top-level fields separated by commas.
            Allow the client to selectively retrieve fields in the response.
    Return:
        Complete Future object.
    """
    return session.get(
        url=f"{connection.base_url}/api/model/tables/{id}",
        headers={
            "X-MSTR-MS-Changeset": changeset_id, "X-MSTR-ProjectID": project_id
        },
        params={"fields": fields},
    )


def get_available_warehouse_tables_async(
    session: FuturesSessionWithRenewal,
    connection: "Connection",
    datasource_id: str,
    namespace_id: str
):
    return session.get(
        f"{connection.base_url}/api/datasources/{datasource_id}/catalog/namespaces/{namespace_id}"
        "/tables",
        headers={
            "X-MSTR-ProjectID": connection.project_id,
        }
    )
